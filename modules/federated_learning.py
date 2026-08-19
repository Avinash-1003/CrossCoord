import torch
from utils.event_bus import bus

class FederatedLearningServer:
    """
    Cloud-based Federated Averaging (FedAvg) Server.
    Collects local PyTorch weights from field agents and averages them
    to create a smarter global model, which is broadcasted back.
    """
    def __init__(self, expected_agents):
        self.expected_agents = expected_agents
        self.agent_weights = {}
        
        bus.subscribe("MODEL_WEIGHTS_UPLOAD", self._on_weights_upload)

    async def _on_weights_upload(self, payload):
        agent_id = payload["agent_id"]
        weights = payload["weights"]
        
        self.agent_weights[agent_id] = weights
        print(f"[FedAvg Server] Received weights from {agent_id}.")
        
        # When all expected agents have uploaded, perform FedAvg
        if len(self.agent_weights) >= self.expected_agents:
            await self._perform_fedavg()

    async def _perform_fedavg(self):
        print("[FedAvg Server] All weights received. Performing Federated Averaging...")
        
        # Initialize averaged weights with the first agent's weights
        avg_weights = {}
        first_key = list(self.agent_weights.keys())[0]
        
        for key in self.agent_weights[first_key].keys():
            avg_weights[key] = self.agent_weights[first_key][key].clone()
            
        # Add the rest
        for agent_id in list(self.agent_weights.keys())[1:]:
            for key in avg_weights.keys():
                avg_weights[key] += self.agent_weights[agent_id][key]
                
        # Divide by total agents to get average
        num_agents = len(self.agent_weights)
        for key in avg_weights.keys():
            avg_weights[key] = torch.div(avg_weights[key], num_agents)
            
        self.agent_weights.clear()
        
        # Broadcast the new global model back to agents
        print("[FedAvg Server] Broadcasting new Global Model...")
        await bus.publish("GLOBAL_MODEL_BROADCAST", {"weights": avg_weights})
