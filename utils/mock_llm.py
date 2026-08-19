import json

class MockLLM:
    """
    Simulates LLM API responses for deterministic local testing.
    """
    def __init__(self):
        # We store predefined responses for specific keywords to simulate
        # the model understanding tasks.
        self.response_map = {
            "disaster_relief": self._mock_disaster_relief,
            "logistics": self._mock_logistics,
            "search_and_rescue": self._mock_search_rescue
        }

    def generate(self, prompt, role="Tier1"):
        """
        Simulates an LLM generation call.
        """
        prompt_lower = prompt.lower()
        
        # Determine the scenario based on keywords
        for key, func in self.response_map.items():
            if key in prompt_lower or key.replace('_', ' ') in prompt_lower:
                return func(role)
                
        # Default fallback
        return json.dumps({
            "status": "error",
            "message": "Unrecognized task domain. Please specify logistics, search_and_rescue, or disaster_relief."
        })

    def _mock_disaster_relief(self, role):
        if role == "Tier1":
            return json.dumps({
                "global_plan": "Respond to disaster relief scenario.",
                "subtasks": [
                    {"id": "task_1", "type": "Aerial_Reconnaissance", "target": (31, 31)},
                    {"id": "task_2", "type": "Ground_Logistics", "target": (10, 10)}
                ]
            })
        elif role == "Tier2":
            return json.dumps({
                "assignments": [
                    {"task_id": "task_1", "assigned_to": "A_003"}, # A_003 is UAV_Quad
                    {"task_id": "task_2", "assigned_to": "A_006"}  # A_006 is UGV_Carrier
                ]
            })

    def _mock_logistics(self, role):
        if role == "Tier1":
            return json.dumps({
                "global_plan": "Execute warehouse logistics operation.",
                "subtasks": [
                    {"id": "task_1", "type": "Ground_Logistics", "target": (15, 20)},
                    {"id": "task_2", "type": "Ground_Inspection", "target": (5, 5)}
                ]
            })
        elif role == "Tier2":
            return json.dumps({
                "assignments": [
                    {"task_id": "task_1", "assigned_to": "A_006"},
                    {"task_id": "task_2", "assigned_to": "A_005"}
                ]
            })

    def _mock_search_rescue(self, role):
        if role == "Tier1":
            return json.dumps({
                "global_plan": "Perform search and rescue in city blocks.",
                "subtasks": [
                    {"id": "task_1", "type": "Aerial_Reconnaissance", "target": (50, 50)},
                    {"id": "task_2", "type": "Aerial_Logistics", "target": (50, 50)}
                ]
            })
        elif role == "Tier2":
            return json.dumps({
                "assignments": [
                    {"task_id": "task_1", "assigned_to": "A_003"},
                    {"task_id": "task_2", "assigned_to": "A_004"}
                ]
            })

if __name__ == "__main__":
    llm = MockLLM()
    print("Testing Tier 1 Mock:")
    print(llm.generate("We have a disaster relief mission requiring scouts and supplies.", role="Tier1"))
    print("\nTesting Tier 2 Mock:")
    print(llm.generate("Allocate tasks for disaster relief.", role="Tier2"))
