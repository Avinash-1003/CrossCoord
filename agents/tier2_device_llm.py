import json

class Tier2DeviceLLM:
    """
    Tier-2 Dispatcher.
    Receives subtasks from Tier-1 and allocates them to Tier-3 physical agents
    based on agent capabilities.
    """
    def __init__(self, llm_backend, agent_registry):
        self.llm = llm_backend
        self.agent_registry = agent_registry  # Dictionary of available Tier-3 agents

    def allocate_tasks(self, subtasks, scenario_context):
        """
        Takes a list of subtasks and assigns them to active agents.
        """
        print(f"[Tier-2 Dispatcher] Allocating {len(subtasks)} tasks...")
        
        # In a real setup, we would inject the agent_registry and subtasks into
        # the prompt so the LLM can make capability-aware decisions.
        prompt = f"Allocate tasks for {scenario_context}. Available agents: {list(self.agent_registry.keys())}"
        
        response = self.llm.generate(prompt, role="Tier2")
        
        try:
            allocations = json.loads(response)
            assignments = allocations.get("assignments", [])
            
            # Map assigned tasks back to the physical agents
            final_schedule = {}
            for assignment in assignments:
                t_id = assignment["task_id"]
                a_id = assignment["assigned_to"]
                
                # Find the matching subtask payload
                task_payload = next((t for t in subtasks if t["id"] == t_id), None)
                
                if task_payload and a_id in self.agent_registry:
                    final_schedule[a_id] = task_payload
                    print(f"  -> Assigned {t_id} to {a_id}")
                else:
                    print(f"  -> Failed to assign {t_id} to {a_id} (Agent offline or invalid)")
                    
            return final_schedule
            
        except json.JSONDecodeError:
            print("[Tier-2 Dispatcher] Failed to parse LLM response as JSON.")
            return {}

if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from utils.mock_llm import MockLLM
    
    mock = MockLLM()
    registry = {"A_003": "UAV_Quad", "A_006": "UGV_Carrier"}
    
    subtasks = [
        {"id": "task_1", "type": "Aerial_Reconnaissance", "target": (31, 31)},
        {"id": "task_2", "type": "Ground_Logistics", "target": (10, 10)}
    ]
    
    dispatcher = Tier2DeviceLLM(mock, registry)
    schedule = dispatcher.allocate_tasks(subtasks, "disaster_relief")
    print("Final Schedule:", schedule)
