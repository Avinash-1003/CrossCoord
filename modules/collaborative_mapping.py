import numpy as np
from utils.event_bus import bus

class CollaborativeMapping:
    """
    Cloud-based Shared Mapping Module.
    Listens for MAP_UPDATE events from agents and maintains a Global Map.
    """
    def __init__(self, h, w):
        self.h = h
        self.w = w
        # -1 = Unknown, 0 = Passable, 1 = Obstacle
        self.global_map = np.full((h, w), -1, dtype=np.int8)
        self.update_count = 0
        
        # Subscribe to agent discoveries
        bus.subscribe("MAP_UPDATE", self._on_map_update)

    async def _on_map_update(self, payload):
        """Handle incoming map data from agents in the field."""
        agent_id = payload["agent_id"]
        obstacles = payload["obstacles"]
        free_spaces = payload["free"]
        
        updated = False
        for r, c in obstacles:
            if self.global_map[r, c] != 1:
                self.global_map[r, c] = 1
                updated = True
                
        for r, c in free_spaces:
            if self.global_map[r, c] != 0:
                self.global_map[r, c] = 0
                updated = True
                
        if updated:
            self.update_count += 1
            # Broadcast the updated global map back to all agents occasionally
            # to prevent flooding the network
            if self.update_count % 5 == 0:
                await bus.publish("GLOBAL_MAP_BROADCAST", {"map": np.copy(self.global_map)})
                
    def get_known_passable(self):
        """Return a list of fully known safe starting positions."""
        return list(zip(*np.where(self.global_map == 0)))
