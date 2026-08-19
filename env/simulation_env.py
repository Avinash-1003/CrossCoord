import numpy as np

class CrossCoordEnv:
    def __init__(self, grid):
        """
        Initializes the simulation environment.
        :param grid: 2D numpy array where 0 is passable and 1 is an obstacle.
        """
        self.grid = grid
        self.height, self.width = grid.shape
        self.hazards = set() # Set of (r, c) tuples
        
    def add_hazard_seed(self, pos):
        """Seed a dynamic hazard (fire/toxic leak) at a position."""
        r, c = pos
        if 0 <= r < self.height and 0 <= c < self.width and self.grid[r, c] == 0:
            self.grid[r, c] = 2 # 2 represents Dynamic Hazard
            self.hazards.add((r, c))

    def expand_hazards(self):
        """Simulate environmental hazard spread (e.g. fire/gas spreading to adjacent free cells)."""
        new_hazards = set()
        for r, c in list(self.hazards):
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.height and 0 <= nc < self.width and self.grid[nr, nc] == 0:
                    self.grid[nr, nc] = 2
                    new_hazards.add((nr, nc))
        self.hazards.update(new_hazards)
        return list(new_hazards)

    def is_valid_pos(self, pos):
        """
        Checks if a position is within bounds and not an obstacle or active hazard.
        """
        r, c = pos
        if r < 0 or r >= self.height or c < 0 or c >= self.width:
            return False
        if self.grid[r, c] in [1, 2]:  # 1 = Obstacle, 2 = Dynamic Hazard
            return False
        return True

    def move_agent(self, agent_id, new_pos):
        """
        Attempts to move an agent to a new position.
        Returns True if successful, False otherwise.
        """
        if agent_id not in self.agents:
            return False
            
        if self.is_valid_pos(new_pos):
            self.agents[agent_id] = new_pos
            return True
            
        return False

    def render(self):
        """
        Returns a string representation of the grid for CLI debugging.
        """
        display = np.full((self.height, self.width), '.', dtype=str)
        display[self.grid == 1] = '@'
        
        for agent_id, (r, c) in self.agents.items():
            display[r, c] = agent_id[-1]  # Just use last char of ID for display
            
        return '\n'.join([''.join(row) for row in display])

if __name__ == "__main__":
    from grid_parser import GridParser
    grid, h, w = GridParser.parse_map("datasets/disaster_relief/random-32-32-20.map")
    env = CrossCoordEnv(grid)
    
    # Add a couple of agents at safe spots
    safe_spots = np.argwhere(grid == 0)
    if len(safe_spots) > 1:
        env.add_agent("A_001", tuple(safe_spots[0]))
        env.add_agent("A_002", tuple(safe_spots[1]))
    
    print("Environment setup complete. Sample render of top-left 10x10:")
    print('\n'.join([''.join(row) for row in env.render().split('\n')[:10]]))
