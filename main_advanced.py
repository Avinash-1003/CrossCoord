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
from utils.llm_client import CrossCoordLLM
from utils.event_bus import bus

async def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║      CROSSCOORD ULTIMATE: DISTRIBUTED MULTI-AGENT        ║")
    print("║ Fog of War | Collaborative Mapping | Federated Learning  ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # Start the event broker in the background
    broker_task = asyncio.create_task(bus.run_broker())
    
    map_file = "datasets/disaster_relief/random-32-32-20.map"
    grid, h, w = GridParser.parse_map(map_file)
    true_env = CrossCoordEnv(grid)
    
    print("[Phase 1] Cloud Booting...")
    # Cloud Modules
    mapper = CollaborativeMapping(h, w)
    fed_server = FederatedLearningServer(expected_agents=4)
    llm = CrossCoordLLM()
    planner = Tier1CloudLLM(llm)
    
    print("[Phase 2] Generating Mission Plan...")
    subtasks = planner.decompose_mission("Conduct advanced distributed disaster relief operations.")
    if not subtasks:
        subtasks = [
            {"id": "task_1", "type": "Aerial_Reconnaissance", "target": (31, 31)},
            {"id": "task_2", "type": "Ground_Logistics", "target": (10, 10)}
        ]

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

    # Give the Event Bus a tiny moment to process the initial MAP_UPDATEs
    await asyncio.sleep(0.5)

    print("\n[Phase 4] LLM Dispatching...")
    dispatcher = Tier2DeviceLLM(llm, agent_registry)
    schedule = dispatcher.allocate_tasks(subtasks, "disaster_relief")
    
    for aid, task in schedule.items():
        tier3_agents[aid].target = task["target"]
        print(f"  -> Dispatched {task['id']} to {aid}")

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

    print("\n============================================================")
    print("  ULTIMATE EVALUATION SUMMARY")
    print("============================================================")
    print(f"  Total Steps Taken:        {step}")
    print(f"  Map Discovery Rate:       {(np.sum(mapper.global_map != -1) / 1024) * 100:.1f}%")
    print(f"  Federated Learning Syncs: {step // tier3_agents['A_003'].sync_interval}")
    print("============================================================\n")

    # Stop broker
    bus.stop()
    broker_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
