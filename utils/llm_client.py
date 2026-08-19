import os
import json
from openai import OpenAI
from openai import AuthenticationError, RateLimitError
from .mock_llm import MockLLM

class CrossCoordLLM:
    """
    Unified LLM Client for CrossCoord.
    Uses OpenAI GPT-4o-mini or GPT-3.5 by default if OPENAI_API_KEY is set.
    Automatically falls back to MockLLM if API key is missing or invalid.
    """
    def __init__(self, api_key=None, model="gpt-4o-mini"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.client = None
        self.fallback = MockLLM()
        self.use_real_llm = False

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.use_real_llm = True
                print(f"[LLM Client] Initialized with real OpenAI API (model: {self.model})")
            except Exception as e:
                print(f"[LLM Client] Error initializing OpenAI client: {e}. Falling back to MockLLM.")
                self.use_real_llm = False
        else:
            print("[LLM Client] No OPENAI_API_KEY found. Using MockLLM fallback.")

    def generate(self, prompt, role="Tier1"):
        """
        Generate a response from the LLM, matching the MockLLM interface.
        """
        if self.use_real_llm and self.client:
            # Construct system prompt based on role
            if role == "Tier1":
                system_prompt = "You are a Tier-1 Cloud LLM Central Planner. Decompose the mission into subtasks. Output strict JSON with a 'subtasks' array containing objects with 'id', 'type', and 'target' (x, y coordinate array)."
            else:
                system_prompt = "You are a Tier-2 Device LLM Dispatcher. Assign tasks to available agents based on capability. Output strict JSON with an 'assignments' array containing objects with 'task_id' and 'assigned_to' (agent ID)."
                
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{prompt}\nEnsure the response is valid JSON."}
            ]

            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.2,
                )
                return completion.choices[0].message.content
            except (AuthenticationError, RateLimitError) as e:
                print(f"[LLM Client] API Error ({e.__class__.__name__}). Falling back to MockLLM.")
                self.use_real_llm = False
                return self.fallback.generate(prompt, role)
            except Exception as e:
                print(f"[LLM Client] Unexpected Error: {e}. Falling back to MockLLM.")
                return self.fallback.generate(prompt, role)
        else:
            return self.fallback.generate(prompt, role)

if __name__ == "__main__":
    llm = CrossCoordLLM()
    res = llm.generate("Test prompt for disaster relief.", role="Tier1")
    print("Response:", res)
