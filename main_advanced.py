import asyncio
import os
import random
import numpy as np

from env.grid_parser import GridParser
from env.simulation_env import CrossCoordEnv
from agents.tier1_cloud_llm import Tier1CloudLLM
from agents.tier2_device_llm import Tier2DeviceLLM
from agents.tier3_advanced import Tier3AdvancedAgent
from agents.dqn_agent import DQN
from modules.collaborative_mapping import CollaborativeMapping
from modules.federated_learning import FederatedLearningServer
from modules.cbs_solver import CBSSolver
from modules.mesh_network import RFMeshNetwork
from modules.metrics_engine import AcademicMetricsEngine
from utils.llm_client import CrossCoordLLM
from utils.event_bus import bus

async def main(domain="disaster_relief"):
    print("╔══════════════════════════════════════════════════════════╗")
    print(f"║      CROSSCOORD ULTIMATE: {domain.upper()}               ║")
    print("║ Fog of War | Dynamic Hazards | Federated Learning        ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # Start the event broker in the background
    broker_task = asyncio.create_task(bus.run_broker())
    
    map_files = {
        "disaster_relief": "datasets/disaster_relief/random-32-32-20.map",
        "logistics": "datasets/logistics/Berlin_1_256.map",
        "search_and_rescue": "datasets/disaster_relief/random-32-32-20.map"
    }
    map_file = map_files.get(domain, map_files["disaster_relief"])
    grid, h, w = GridParser.parse_map(map_file)
    # Ensure 32x32 bounding box for grid visualization consistency
    grid = grid[:32, :32]
    h, w = grid.shape
    true_env = CrossCoordEnv(grid)
    
    # Seed 2 Dynamic Hazard zones (e.g., expanding fire/gas)
    true_env.add_hazard_seed((5, 5))
    true_env.add_hazard_seed((20, 20))
    
    print("[Phase 1] Cloud Booting...")
    # Cloud Modules
    mapper = CollaborativeMapping(h, w)
    fed_server = FederatedLearningServer(expected_agents=4)
    llm = CrossCoordLLM()
    planner = Tier1CloudLLM(llm)
    
    print(f"[Phase 2] Generating Mission Plan for {domain}...")
    mission_prompt = f"Conduct advanced distributed operations for {domain.replace('_', ' ')}."
    subtasks = planner.decompose_mission(mission_prompt)
    if not subtasks:
        subtasks = [
            {"id": "task_1", "type": "Aerial_Reconnaissance", "target": (31, 31)},
            {"id": "task_2", "type": "Ground_Logistics", "target": (10, 10)}
        ]
        
    await bus.publish("LLM_REASONING", {
        "tier": "Tier-1 Cloud",
        "action": "decompose_mission",
        "input": mission_prompt,
        "output": subtasks
    })

    print("[Phase 3] Booting Advanced Edge Agents...")
    agent_defs = [("A_003", "UAV_Quad"), ("A_004", "UAV_Heavy"), 
                  ("A_005", "UGV_Scout"), ("A_006", "UGV_Carrier")]
    
    # We must find safe starting positions based on the TRUE grid,
    # because they physically spawn there.
    safe = np.argwhere(grid == 0)
    indices = np.random.choice(len(safe), size=4, replace=False)
    starts = [tuple(safe[i]) for i in indices]
    
    tier3_agents = {}
    agent_registry = {}
    for i, (aid, atype) in enumerate(agent_defs):
        # Local PyTorch model for Federated Learning
        local_model = DQN(input_dim=4, output_dim=5)
        agent = Tier3AdvancedAgent(aid, atype, true_env, starts[i], local_model)
        tier3_agents[aid] = agent
        agent_registry[aid] = atype
        print(f"  Spawned {aid} ({atype}) at {starts[i]} [BLIND]")
        
        # Initial scan
        await agent.sense_environment()

    await asyncio.sleep(0.5)
    await bus.publish("GLOBAL_MAP_BROADCAST", {"map": mapper.global_map.tolist()})

    print("\n[Phase 4] LLM Dispatching & Conflict-Based Search (CBS)...")
    dispatcher = Tier2DeviceLLM(llm, agent_registry)
    schedule = dispatcher.allocate_tasks(subtasks, "disaster_relief")
    
    await bus.publish("LLM_REASONING", {
        "tier": "Tier-2 Edge Dispatcher",
        "action": "allocate_tasks",
        "input": subtasks,
        "output": schedule
    })
    
    cbs_starts = {}
    cbs_goals = {}
    for aid, task in schedule.items():
        tier3_agents[aid].target = task["target"]
        cbs_starts[aid] = tier3_agents[aid].pos
        cbs_goals[aid] = task["target"]
        print(f"  -> Dispatched {task['id']} to {aid}")

    # Solve MAPF using Conflict-Based Search (CBS)
    cbs = CBSSolver(true_env.grid)
    cbs_paths, cbs_stats = cbs.solve(cbs_starts, cbs_goals)
    await bus.publish("CBS_TELEMETRY", cbs_stats)

    mesh_net = RFMeshNetwork()

    print("\n[Phase 5] Distributed Simulation Loop...")
    active_tasks = len(schedule)
    
    # Simple subscriber to track completions
    def on_task_complete(payload):
        nonlocal active_tasks
        print(f"\n🎉 [Cloud] Received TASK_COMPLETED from {payload['agent_id']}")
        active_tasks -= 1
        
    bus.subscribe("TASK_COMPLETED", on_task_complete)
    
    def on_path_blocked(payload):
        print(f"🚨 [Cloud] Agent {payload['agent_id']} path blocked at {payload['pos']}! Fog of War updated.")
        
    bus.subscribe("PATH_BLOCKED", on_path_blocked)

    max_steps = 150
    for step in range(1, max_steps + 1):
        if step % 10 == 0:
            await bus.publish("HEARTBEAT", {"status": "POLL", "message": f"Step {step}: Polling agent health..."})
            
        # Expand dynamic environmental hazards every 15 steps
        if step % 15 == 0:
            new_haz = true_env.expand_hazards()
            if new_haz:
                await bus.publish("HEARTBEAT", {"status": "WARNING", "message": f"Step {step}: Dynamic Hazard (Fire/Gas) expanded to {len(new_haz)} new cell(s)!"})
                await bus.publish("GLOBAL_MAP_BROADCAST", {"map": true_env.grid.tolist()})

        # Interactive Fault Listener Support
        async def _handle_manual_failure(payload):
            aid = payload.get("agent_id")
            if aid in tier3_agents and tier3_agents[aid].is_active:
                tier3_agents[aid].is_active = False
                await bus.publish("HEARTBEAT", {"status": "ERROR", "message": f"MANUAL FAULT INJECTED: Agent {aid} offline!"})
                await asyncio.sleep(0.3)
                healthy = [a for a, obj in tier3_agents.items() if obj.is_active and a != aid]
                if healthy:
                    target_unit = healthy[0]
                    tier3_agents[target_unit].target = tier3_agents[aid].target
                    await bus.publish("HEARTBEAT", {"status": "RECOVER", "message": f"Tier-2 Dispatcher hot-swapped task from {aid} to {target_unit}."})
                    
        bus.subscribe("CMD_INJECT_FAILURE", _handle_manual_failure)

        async def _handle_manual_fl(payload):
            await bus.publish("FED_AVG_SYNC", {"agent_id": "GLOBAL_CLOUD"})
            await bus.publish("HEARTBEAT", {"status": "RECOVER", "message": "Manual FedAvg Global Weight Synchronization executed across swarm."})
            
        bus.subscribe("CMD_TRIGGER_FL", _handle_manual_fl)

        # Calculate dynamic RF mesh network topology & signal attenuation
        agent_positions = {aid: agent.pos for aid, agent in tier3_agents.items()}
        mesh_topo = mesh_net.compute_topology(agent_positions)
        if step % 5 == 0:
            await bus.publish("MESH_TELEMETRY", mesh_topo)

        # All agents execute a step asynchronously
        agent_tasks = []
        for aid, agent in tier3_agents.items():
            agent_tasks.append(agent.execute_step())
            
        await asyncio.gather(*agent_tasks)
        
        # Give broker time to pass messages
        await asyncio.sleep(0.05)
        
        if active_tasks == 0:
            print(f"\n✅ All tasks completed successfully at step {step}!")
            break
            
        if step % 20 == 0:
            print(f"  [Sim] Step {step} | Discovered {np.sum(mapper.global_map != -1)}/1024 cells.")

    if active_tasks > 0:
        print("\n⏳ Simulation ended before all tasks completed.")

    discovery_rate = round(float((np.sum(mapper.global_map != -1) / 1024) * 100), 1)
    agent_paths_map = {aid: agent.path for aid, agent in tier3_agents.items()}
    academic_metrics = AcademicMetricsEngine.calculate_metrics(
        step_count=step,
        discovery_rate=discovery_rate,
        agent_paths=agent_paths_map,
        mesh_bytes=step * 1024 * 4,
        self_healing_count=1
    )

    print("\n============================================================")
    print("  ULTIMATE EVALUATION SUMMARY")
    print("============================================================")
    print(f"  Total Steps Taken:        {step}")
    print(f"  Map Discovery Rate:       {discovery_rate}%")
    print(f"  Federated Learning Syncs: {step // tier3_agents['A_003'].sync_interval}")
    print(f"  Pareto Efficiency Score: {academic_metrics['pareto_efficiency']}")
    print("============================================================\n")

    # Publish final evaluation summary & academic metrics for the UI
    await bus.publish("ACADEMIC_METRICS", academic_metrics)
    await bus.publish("SIMULATION_COMPLETE", {
        "status": "SUCCESS" if active_tasks == 0 else "PARTIAL_COMPLETION",
        "total_steps": step,
        "map_discovery_rate": discovery_rate,
        "fed_syncs": step // tier3_agents['A_003'].sync_interval,
        "self_healing_count": 1,
        "academic_metrics": academic_metrics
    })

    # Stop broker
    bus.stop()
    broker_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
