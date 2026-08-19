import heapq

class Tier3Executor:
    """
    Tier-3 Agent: Physical Executor (UAV/UGV).
    Handles pathfinding and physical execution of subtasks.
    """
    def __init__(self, agent_id, agent_type, env, start_pos):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.env = env
        self.pos = start_pos
        self.path = []
        self.is_active = True  # Used for self-healing dropout tests
        
        self.env.add_agent(agent_id, start_pos)

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def compute_path(self, goal_pos):
        """
        A* pathfinding algorithm.
        """
        start = self.pos
        if not self.env.is_valid_pos(goal_pos):
            return False

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal_pos:
                break

            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_pos = (current[0] + dr, current[1] + dc)
                if self.env.is_valid_pos(next_pos):
                    new_cost = cost_so_far[current] + 1
                    if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                        cost_so_far[next_pos] = new_cost
                        priority = new_cost + self.heuristic(goal_pos, next_pos)
                        heapq.heappush(frontier, (priority, next_pos))
                        came_from[next_pos] = current

        # Reconstruct path
        if goal_pos not in came_from:
            return False # No path found
            
        curr = goal_pos
        path = []
        while curr != start:
            path.append(curr)
            curr = came_from[curr]
            
        path.reverse()
        self.path = path
        return True

    def step(self):
        """
        Take one step along the computed path.
        """
        if not self.is_active:
            return "FAILED"
            
        if not self.path:
            return "IDLE"

        next_pos = self.path[0]
        if self.env.move_agent(self.agent_id, next_pos):
            self.pos = next_pos
            self.path.pop(0)
            return "MOVING"
        else:
            return "BLOCKED"

if __name__ == "__main__":
    import sys
    sys.path.append('.')
    from env.grid_parser import GridParser
    from env.simulation_env import CrossCoordEnv
    
    grid, _, _ = GridParser.parse_map("datasets/disaster_relief/random-32-32-20.map")
    env = CrossCoordEnv(grid)
    
    start = (0, 0)
    # Find a valid start and end
    while grid[start] == 1: start = (start[0], start[1]+1)
    
    goal = (31, 31)
    while grid[goal] == 1: goal = (goal[0], goal[1]-1)
    
    agent = Tier3Executor("UAV_1", "UAV_Quad", env, start)
    success = agent.compute_path(goal)
    print(f"Path computed: {success}, steps: {len(agent.path)}")
    
    steps = 0
    while agent.step() == "MOVING":
        steps += 1
    
    print(f"Agent reached goal in {steps} steps. Current pos: {agent.pos}")
