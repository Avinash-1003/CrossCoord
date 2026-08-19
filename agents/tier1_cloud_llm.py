import json

class Tier1CloudLLM:
    """
    Tier-1 Central Planner.
    Responsible for receiving a global mission prompt and decomposing it
    into distinct subtasks.
    """
    def __init__(self, llm_backend):
        self.llm = llm_backend

    def decompose_mission(self, mission_prompt):
        """
        Takes a natural language prompt and returns a list of subtasks.
        """
        print(f"[Tier-1 Cloud] Processing mission: '{mission_prompt}'")
        
        # In a real system, we would inject a system prompt here
        # instructing the LLM to output a specific JSON schema.
        response = self.llm.generate(mission_prompt, role="Tier1")
        
        try:
            plan = json.loads(response)
            if "status" in plan and plan["status"] == "error":
                print(f"[Tier-1 Cloud] Error: {plan['message']}")
                return []
                
            print(f"[Tier-1 Cloud] Successfully generated {len(plan['subtasks'])} subtasks.")
            return plan['subtasks']
            
        except json.JSONDecodeError:
            print("[Tier-1 Cloud] Failed to parse LLM response as JSON.")
            return []

if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from utils.mock_llm import MockLLM
    
    mock = MockLLM()
    planner = Tier1CloudLLM(mock)
    subtasks = planner.decompose_mission("Conduct disaster relief operations.")
    print("Subtasks:", subtasks)
