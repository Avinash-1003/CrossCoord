#!/usr/bin/env python3
"""
CrossCoord: Main Execution Pipeline

Runs a full multi-agent mission demonstrating:
  1. Transfer/Adaptation to an unseen domain (disaster_relief)
  2. Tier-1 Cloud LLM task decomposition
  3. Tier-2 Device LLM task dispatching
  4. Tier-3 physical agent execution with A* pathfinding
  5. Self-Healing coordination under agent failures
  6. Full evaluation metrics report
"""

import sys
import os
import numpy as np
import json

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env.grid_parser import GridParser
from env.simulation_env import CrossCoordEnv
from agents.tier1_cloud_llm import Tier1CloudLLM
from agents.tier2_device_llm import Tier2DeviceLLM
from agents.tier3_executor import Tier3Executor
from modules.self_healing import SelfHealingCoordinator
from modules.transfer_adaptation import TransferAdaptationModule
from utils.llm_client import CrossCoordLLM
from utils.metrics import MetricsTracker


def find_safe_positions(grid, count):
    """Find 'count' random passable positions on the grid."""
    safe = np.argwhere(grid == 0)
    indices = np.random.choice(len(safe), size=min(count, len(safe)), replace=False)
    return [tuple(safe[i]) for i in indices]


def run_mission(scenario, map_file, max_steps=500, failure_rate=0.02):
    """
    Run a complete CrossCoord mission.
    """
    print("\n" + "=" * 60)
    print(f"  CROSSCOORD MISSION: {scenario.upper()}")
    print("=" * 60)

    # ─── Initialize Metrics ───────────────────────────────────────
    metrics = MetricsTracker()
    metrics.start_mission()

    # ─── Phase: Transfer/Adaptation ───────────────────────────────
    print("\n[Phase] Transfer/Adaptation Module")
    tam = TransferAdaptationModule()

    # Transfer to target domain (possibly unseen)
    domain_config = {
        "map_file": map_file,
        "obstacle_density": 0.20,
        "hazards": ["flooding", "structural_collapse"],
    }
    bundle = tam.transfer_to_domain(scenario, domain_config)
    if not bundle:
        print("Transfer failed. Aborting mission.")
        return

    # ─── Load Environment ─────────────────────────────────────────
    print(f"\n[Phase] Loading environment from {map_file}")
    grid, h, w = GridParser.parse_map(map_file)
    domain_config["grid_size"] = (h, w)
    env = CrossCoordEnv(grid)
    print(f"  Grid: {h}x{w}, obstacles: {np.sum(grid)}, passable: {h*w - np.sum(grid)}")

    # ─── Phase: Tier-1 Cloud LLM ──────────────────────────────────
    print("\n[Phase] Tier-1 Cloud LLM — Task Decomposition")
    llm = CrossCoordLLM()
    planner = Tier1CloudLLM(llm)
    subtasks = planner.decompose_mission(f"Conduct {scenario.replace('_', ' ')} operations.")
    metrics.log_llm_call()

    if not subtasks:
        print("No subtasks generated. Aborting.")
        return

    # ─── Spawn Tier-3 Agents ──────────────────────────────────────
    print("\n[Phase] Spawning Tier-3 agents")
    safe_positions = find_safe_positions(grid, 4)

    agent_defs = [
        ("A_003", "UAV_Quad"),
        ("A_004", "UAV_Heavy"),
        ("A_005", "UGV_Scout"),
        ("A_006", "UGV_Carrier"),
    ]

    tier3_agents = {}
    for i, (aid, atype) in enumerate(agent_defs):
        pos = safe_positions[i % len(safe_positions)]
        agent = Tier3Executor(aid, atype, env, pos)
        tier3_agents[aid] = agent
        print(f"  Spawned {aid} ({atype}) at {pos}")

    # ─── Phase: Tier-2 Device LLM ─────────────────────────────────
    print("\n[Phase] Tier-2 Device LLM — Task Dispatching")
    agent_registry = {aid: agent.agent_type for aid, agent in tier3_agents.items()}
    dispatcher = Tier2DeviceLLM(llm, agent_registry)
    schedule = dispatcher.allocate_tasks(subtasks, scenario)
    metrics.log_llm_call()

    for aid in schedule:
        metrics.log_task_assigned()

    # ─── Phase: Self-Healing Setup ────────────────────────────────
    print("\n[Phase] Self-Healing Coordinator — Armed")
    healer = SelfHealingCoordinator(dispatcher, {
        aid: failure_rate for aid in tier3_agents
    })
    for aid in tier3_agents:
        healer.register_agent(aid, failure_rate)

    # ─── Compute Initial Paths ────────────────────────────────────
    print("\n[Phase] Computing initial A* paths")
    for aid, task in schedule.items():
        target = task["target"]
        if isinstance(target, list):
            target = tuple(target)

        # Clamp target to valid grid range
        target = (min(target[0], h - 1), min(target[1], w - 1))

        # If target is an obstacle, find nearest passable cell
        if grid[target] == 1:
            safe = np.argwhere(grid == 0)
            dists = np.abs(safe[:, 0] - target[0]) + np.abs(safe[:, 1] - target[1])
            target = tuple(safe[np.argmin(dists)])

        task["target"] = target
        success = tier3_agents[aid].compute_path(target)
        status = f"{len(tier3_agents[aid].path)} steps" if success else "NO PATH"
        print(f"  {aid} -> target {target}: {status}")

    # ─── Simulation Loop ──────────────────────────────────────────
    print(f"\n[Phase] Simulation running (max {max_steps} steps)...")
    for step in range(1, max_steps + 1):
        # 1. Heartbeat check (may trigger failures)
        failed = healer.heartbeat_check(tier3_agents, step)

        # 2. Redistribute if failures occurred
        if failed:
            schedule = healer.redistribute_tasks(
                failed, schedule, tier3_agents, scenario
            )
            metrics.log_llm_call()  # Partial replan counts as an LLM call

        # 3. Step each active agent
        all_idle = True
        for aid, agent in tier3_agents.items():
            if not agent.is_active:
                continue

            status = agent.step()
            if status == "MOVING":
                metrics.log_agent_step(aid)
                all_idle = False
            elif status == "IDLE" and aid in schedule:
                # Agent reached its target
                metrics.log_task_completed(aid)
                del schedule[aid]  # Task done
            elif status == "BLOCKED":
                all_idle = False  # Still trying

        # 4. Check completion
        if all_idle and not schedule:
            print(f"\n  ✅ All tasks completed at step {step}!")
            break
    else:
        print(f"\n  ⏱️  Max steps ({max_steps}) reached.")

    # ─── Report ───────────────────────────────────────────────────
    metrics.end_mission()
    report = metrics.compute_report(
        self_healing_metrics=healer.get_metrics(),
        transfer_metrics=tam.get_metrics(),
    )
    metrics.print_report(report)

    # Save report to JSON
    report_file = f"results_{scenario}.json"
    # Convert non-serializable items
    def make_serializable(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, tuple):
            return list(obj)
        return obj

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=make_serializable)
    print(f"\n  Report saved to: {report_file}")

    return report


if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          CROSSCOORD FRAMEWORK v1.0                      ║")
    print("║  Transferable, Self-Healing Multi-Agent Coordination    ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Run on the unseen disaster relief domain (zero-shot transfer)
    run_mission(
        scenario="disaster_relief",
        map_file="datasets/disaster_relief/random-32-32-20.map",
        max_steps=300,
        failure_rate=0.03,  # 3% chance of failure per step per agent
    )

    print("\n\n")

    # Run on a known domain for comparison
    run_mission(
        scenario="logistics",
        map_file="datasets/logistics/Berlin_1_256.map",
        max_steps=1000,
        failure_rate=0.01,  # Lower failure rate for comparison
    )
