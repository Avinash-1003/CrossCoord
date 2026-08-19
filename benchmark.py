#!/usr/bin/env python3
"""
CrossCoord Benchmark Suite

Runs systematic evaluations across all domains with multiple failure rates,
trains Q-Learning agents, generates comparison plots and a full report.
"""

import sys
import os
import json
import numpy as np
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env.grid_parser import GridParser
from env.simulation_env import CrossCoordEnv
from agents.tier1_cloud_llm import Tier1CloudLLM
from agents.tier2_device_llm import Tier2DeviceLLM
from agents.tier3_executor import Tier3Executor
from agents.q_learning_agent import QLearningAgent, train_agent_on_map
from modules.self_healing import SelfHealingCoordinator
from modules.transfer_adaptation import TransferAdaptationModule
from utils.mock_llm import MockLLM
from utils.metrics import MetricsTracker
from utils.visualizer import Visualizer
from utils.config import load_config, save_default_config


def find_safe_positions(grid, count):
    safe = np.argwhere(grid == 0)
    indices = np.random.choice(len(safe), size=min(count, len(safe)), replace=False)
    return [tuple(safe[i]) for i in indices]


def run_benchmark_mission(scenario, map_file, max_steps=500, failure_rate=0.02,
                          use_ql=False, ql_agent=None, fig_dir="results/figures",
                          seed=42):
    """Run a single benchmark mission and return the report."""
    random.seed(seed)
    np.random.seed(seed)

    metrics = MetricsTracker()
    metrics.start_mission()

    # Transfer/Adaptation
    tam = TransferAdaptationModule()
    tam.register_domain("logistics", {
        "map_file": "datasets/logistics/Berlin_1_256.map",
        "grid_size": (256, 256), "obstacle_density": 0.15,
    })
    tam.register_domain("search_and_rescue", {
        "map_file": "datasets/search_and_rescue/Boston_0_256.map",
        "grid_size": (256, 256), "obstacle_density": 0.25,
    })

    domain_config = {
        "map_file": map_file, "obstacle_density": 0.20,
        "hazards": ["flooding", "structural_collapse"],
    }
    bundle = tam.transfer_to_domain(scenario, domain_config)
    if not bundle:
        return None

    # Load environment
    grid, h, w = GridParser.parse_map(map_file)
    env = CrossCoordEnv(grid)

    # Tier-1
    llm = MockLLM()
    planner = Tier1CloudLLM(llm)
    subtasks = planner.decompose_mission(f"Conduct {scenario.replace('_', ' ')} operations.")
    metrics.log_llm_call()
    if not subtasks:
        return None

    # Spawn Tier-3
    safe_positions = find_safe_positions(grid, 4)
    agent_defs = [
        ("A_003", "UAV_Quad"), ("A_004", "UAV_Heavy"),
        ("A_005", "UGV_Scout"), ("A_006", "UGV_Carrier"),
    ]
    tier3_agents = {}
    for i, (aid, atype) in enumerate(agent_defs):
        pos = safe_positions[i % len(safe_positions)]
        agent = Tier3Executor(aid, atype, env, pos)
        tier3_agents[aid] = agent

    # Tier-2
    agent_registry = {aid: agent.agent_type for aid, agent in tier3_agents.items()}
    dispatcher = Tier2DeviceLLM(llm, agent_registry)
    schedule = dispatcher.allocate_tasks(subtasks, scenario)
    metrics.log_llm_call()
    for aid in schedule:
        metrics.log_task_assigned()

    # Self-Healing
    healer = SelfHealingCoordinator(dispatcher, {aid: failure_rate for aid in tier3_agents})
    for aid in tier3_agents:
        healer.register_agent(aid, failure_rate)

    # Compute paths
    for aid, task in schedule.items():
        target = task["target"]
        if isinstance(target, list):
            target = tuple(target)
        target = (min(target[0], h - 1), min(target[1], w - 1))
        if grid[target] == 1:
            safe = np.argwhere(grid == 0)
            dists = np.abs(safe[:, 0] - target[0]) + np.abs(safe[:, 1] - target[1])
            target = tuple(safe[np.argmin(dists)])
        task["target"] = target

        if use_ql and ql_agent:
            path = ql_agent.get_learned_path(tier3_agents[aid].pos, target)
            tier3_agents[aid].path = path[1:]  # Skip current position
        else:
            tier3_agents[aid].compute_path(target)

    # Collect initial state for visualization
    initial_agents = {}
    initial_goals = {}
    initial_paths = {}
    for aid, agent in tier3_agents.items():
        initial_agents[aid] = (agent.pos[0], agent.pos[1], agent.agent_type, agent.is_active)
        initial_paths[aid] = list(agent.path)
    for aid, task in schedule.items():
        initial_goals[aid] = task["target"]

    # Save initial snapshot
    Visualizer.render_grid_snapshot(
        grid, initial_agents, initial_goals, initial_paths,
        title=f"CrossCoord — {scenario.replace('_', ' ').title()} (Initial)",
        save_path=os.path.join(fig_dir, f"{scenario}_initial.png"),
        step_num=0
    )

    # Simulation loop
    for step in range(1, max_steps + 1):
        failed = healer.heartbeat_check(tier3_agents, step)
        if failed:
            schedule = healer.redistribute_tasks(failed, schedule, tier3_agents, scenario)
            metrics.log_llm_call()

        all_idle = True
        for aid, agent in tier3_agents.items():
            if not agent.is_active:
                continue
            status = agent.step()
            if status == "MOVING":
                metrics.log_agent_step(aid)
                all_idle = False
            elif status == "IDLE" and aid in schedule:
                metrics.log_task_completed(aid)
                del schedule[aid]
            elif status == "BLOCKED":
                all_idle = False

        if all_idle and not schedule:
            break

    # Save final snapshot
    final_agents = {}
    for aid, agent in tier3_agents.items():
        final_agents[aid] = (agent.pos[0], agent.pos[1], agent.agent_type, agent.is_active)
    Visualizer.render_grid_snapshot(
        grid, final_agents, initial_goals, {},
        title=f"CrossCoord — {scenario.replace('_', ' ').title()} (Final)",
        save_path=os.path.join(fig_dir, f"{scenario}_final.png"),
        step_num=step
    )

    # Self-healing timeline
    sh_metrics = healer.get_metrics()
    if sh_metrics['failure_log']:
        Visualizer.plot_self_healing_timeline(
            sh_metrics['failure_log'], sh_metrics['recovery_log'], step,
            save_path=os.path.join(fig_dir, f"{scenario}_healing_timeline.png")
        )

    metrics.end_mission()
    report = metrics.compute_report(
        self_healing_metrics=sh_metrics,
        transfer_metrics=tam.get_metrics(),
    )
    return report


def run_full_benchmark():
    """Run the complete benchmark suite."""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        CROSSCOORD BENCHMARK SUITE v1.0                  ║")
    print("╚══════════════════════════════════════════════════════════╝")

    config = load_config()
    save_default_config()

    os.makedirs("results", exist_ok=True)
    os.makedirs("results/figures", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # ─── Phase A: Q-Learning Training ─────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE A: Q-Learning Agent Training")
    print("=" * 60)

    ql_agent = train_agent_on_map(
        map_file="datasets/disaster_relief/random-32-32-20.map",
        agent_id="QL_DisasterRelief",
        episodes=config["q_learning"]["episodes"],
        save_path="models/ql_disaster_relief.pkl",
    )

    # Plot training curves
    Visualizer.plot_training_curves(
        ql_agent.episode_rewards, ql_agent.episode_lengths,
        "QL_DisasterRelief",
        save_path="results/figures/ql_training_curves.png"
    )

    # ─── Phase B: Benchmark Missions ──────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE B: Running Benchmark Missions")
    print("=" * 60)

    scenarios = [
        ("disaster_relief", "datasets/disaster_relief/random-32-32-20.map", 300),
        ("logistics", "datasets/logistics/Berlin_1_256.map", 1000),
        ("search_and_rescue", "datasets/search_and_rescue/Boston_0_256.map", 1000),
    ]

    failure_rates = [0.00, 0.02, 0.05]
    all_results = {}

    for scenario, map_file, max_steps in scenarios:
        for fr in failure_rates:
            label = f"{scenario}_fr{int(fr*100):02d}"
            print(f"\n--- Running: {label} ---")

            use_ql = (scenario == "disaster_relief")
            report = run_benchmark_mission(
                scenario, map_file, max_steps=max_steps,
                failure_rate=fr, use_ql=use_ql,
                ql_agent=ql_agent if use_ql else None,
                fig_dir=f"results/figures/{label}",
                seed=42,
            )

            if report:
                all_results[label] = report
                report_file = f"results/{label}.json"
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)

    # ─── Phase C: Comparison Plots ────────────────────────────────
    print("\n" + "=" * 60)
    print("  PHASE C: Generating Comparison Plots")
    print("=" * 60)

    # 1. Task accuracy across scenarios (no failure)
    no_fail = {k: v for k, v in all_results.items() if k.endswith("_fr00")}
    if no_fail:
        Visualizer.plot_benchmark_comparison(
            no_fail, "task_accuracy.accuracy_pct",
            "Task Accuracy by Domain (No Failures)",
            "Accuracy (%)",
            save_path="results/figures/accuracy_no_failure.png"
        )

    # 2. Task accuracy under 5% failure
    high_fail = {k: v for k, v in all_results.items() if k.endswith("_fr05")}
    if high_fail:
        Visualizer.plot_benchmark_comparison(
            high_fail, "task_accuracy.accuracy_pct",
            "Task Accuracy by Domain (5% Failure Rate)",
            "Accuracy (%)",
            save_path="results/figures/accuracy_high_failure.png"
        )

    # 3. Communication overhead
    if no_fail:
        Visualizer.plot_benchmark_comparison(
            no_fail, "communication_overhead.total_llm_calls",
            "Communication Overhead by Domain",
            "Total LLM Calls",
            save_path="results/figures/comm_overhead.png"
        )

    # 4. Radar chart — no failure vs high failure for disaster relief
    radar_data = {}
    for key in ["disaster_relief_fr00", "disaster_relief_fr05"]:
        if key in all_results:
            radar_data[key] = all_results[key]
    if len(radar_data) >= 2:
        Visualizer.plot_transfer_comparison(
            radar_data,
            save_path="results/figures/radar_comparison.png"
        )

    # ─── Phase D: Summary ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  BENCHMARK COMPLETE — SUMMARY")
    print("=" * 60)

    for label, report in all_results.items():
        ta = report['task_accuracy']
        sh = report.get('self_healing', {})
        tr = report.get('transfer_adaptation', {})
        print(f"\n  {label}:")
        print(f"    Accuracy: {ta['accuracy_pct']}%  |  "
              f"LLM Calls: {report['communication_overhead']['total_llm_calls']}  |  "
              f"Failures: {sh.get('total_failures', 0)}  |  "
              f"Recoveries: {sh.get('successful_recoveries', 0)}  |  "
              f"Transfer: {tr.get('zero_shot_transfers', 0)} zero-shot")

    # Save master results
    with open("results/benchmark_summary.json", 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  All results saved to: results/")
    print(f"  All figures saved to: results/figures/")


if __name__ == "__main__":
    run_full_benchmark()
