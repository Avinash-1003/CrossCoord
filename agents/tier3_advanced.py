import asyncio
import numpy as np
from utils.event_bus import bus

class Tier3AdvancedAgent:
    """
    Advanced Tier-3 Agent with:
    - Asynchronous Execution
    - Fog of War (Limited Sensor Radius)
    - Collaborative Mapping (Publishes MAP_UPDATE)
    - Federated Learning Hooks
    """
    def __init__(self, agent_id, agent_type, true_env, start_pos, local_model=None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        
        # Ground truth environment (for sensors only)
        self.true_env = true_env
        self.h, self.w = true_env.grid.shape
        
        # Local knowledge of the map (Fog of War)
        # 0 = Passable, 1 = Obstacle, -1 = Unknown
        self.local_map = np.full((self.h, self.w), -1, dtype=np.int8)
        
        self.pos = start_pos
        self.sensor_radius = 5  # Can see a 11x11 grid around itself
        self.is_active = True
        
        # Navigation
        self.target = None
        self.path = []
        
        # FL specific
        self.local_model = local_model
        self.steps_since_sync = 0
        self.sync_interval = 20
        
        # Subscribe to new global maps
        bus.subscribe("GLOBAL_MAP_BROADCAST", self._on_global_map)
        bus.subscribe("GLOBAL_MODEL_BROADCAST", self._on_global_model)

    def _on_global_map(self, payload):
        """Update local map with the shared global map from the Cloud."""
        shared_map = payload["map"]
        # Merge knowledge (keep obstacles if global map knows about them)
        mask = shared_map != -1
        self.local_map[mask] = shared_map[mask]

    def _on_global_model(self, payload):
        """Update local PyTorch model with FedAvg global weights."""
        if self.local_model:
            print(f"[{self.agent_id}] Received updated FedAvg Global Model.")
            self.local_model.load_state_dict(payload["weights"])

    async def sense_environment(self):
        """Discover the true grid within sensor radius and publish updates."""
        discovered_obstacles = []
        discovered_free = []
        
        r_start = max(0, self.pos[0] - self.sensor_radius)
        r_end = min(self.h, self.pos[0] + self.sensor_radius + 1)
        c_start = max(0, self.pos[1] - self.sensor_radius)
        c_end = min(self.w, self.pos[1] + self.sensor_radius + 1)
        
        for r in range(r_start, r_end):
            for c in range(c_start, c_end):
                if self.local_map[r, c] == -1:
                    true_val = self.true_env.grid[r, c]
                    self.local_map[r, c] = true_val
                    if true_val == 1:
                        discovered_obstacles.append((r, c))
                    else:
                        discovered_free.append((r, c))
                        
        if discovered_obstacles or discovered_free:
            # Publish MAP_UPDATE event
            await bus.publish("MAP_UPDATE", {
                "agent_id": self.agent_id,
                "obstacles": discovered_obstacles,
                "free": discovered_free
            })

    async def execute_step(self):
        """One step of the async agent loop."""
        if not self.is_active or not self.target:
            return "IDLE"
            
        await self.sense_environment()
        
        # Basic Navigation using current local knowledge
        if not self.path:
            self._compute_path_local()
            
        if not self.path:
            # Path is blocked by newly discovered obstacle
            await bus.publish("PATH_BLOCKED", {"agent_id": self.agent_id, "pos": self.pos})
            return "BLOCKED"
            
        next_step = self.path.pop(0)
        
        # Check if next step is an obstacle or dynamic hazard
        if self.true_env.grid[next_step] in [1, 2]:
            self.local_map[next_step] = self.true_env.grid[next_step]
            self.path = []
            await bus.publish("PATH_BLOCKED", {"agent_id": self.agent_id, "pos": self.pos})
            return "BLOCKED"
            
        self.pos = next_step
        await bus.publish("AGENT_MOVED", {"agent_id": self.agent_id, "pos": self.pos})
        
        # Calculate distance-based reward & loss for live telemetry
        dist = abs(self.pos[0] - self.target[0]) + abs(self.pos[1] - self.target[1])
        step_reward = -0.5 - (dist * 0.1)
        simulated_loss = max(0.01, 1.5 / (1.0 + (150 - dist) * 0.05))
        
        await bus.publish("DQN_TELEMETRY", {
            "agent_id": self.agent_id,
            "state": [self.pos[0], self.pos[1], self.target[0], self.target[1]],
            "q_values": np.random.uniform(-1, 10, size=5).tolist(),
            "action": "MOVE",
            "loss": round(simulated_loss, 4),
            "reward": round(step_reward, 2)
        })
        
        # FL Sync Logic
        if self.local_model:
            self.steps_since_sync += 1
            if self.steps_since_sync >= self.sync_interval:
                await bus.publish("MODEL_WEIGHTS_UPLOAD", {
                    "agent_id": self.agent_id,
                    "weights": self.local_model.state_dict()
                })
                self.steps_since_sync = 0
        
        if self.pos == self.target:
            self.target = None
            await bus.publish("TASK_COMPLETED", {"agent_id": self.agent_id})
            return "IDLE"
            
        return "MOVING"

    def _compute_path_local(self):
        """A* pathfinding using the incomplete local map."""
        # Simple A* assuming unknown space (-1) is passable.
        from heapq import heappush, heappop
        
        start = self.pos
        goal = self.target
        
        open_set = []
        heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: abs(start[0] - goal[0]) + abs(start[1] - goal[1])}
        
        while open_set:
            current = heappop(open_set)[1]
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                self.path = path[::-1]
                return
                
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                neighbor = (current[0] + dr, current[1] + dc)
                if 0 <= neighbor[0] < self.h and 0 <= neighbor[1] < self.w:
                    # Treat unknown (-1) as passable to encourage exploration
                    if self.local_map[neighbor] == 1:
                        continue
                        
                    tentative_g = g_score[current] + 1
                    if tentative_g < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f = tentative_g + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                        f_score[neighbor] = f
                        heappush(open_set, (f, neighbor))
        
        self.path = [] # No path found
