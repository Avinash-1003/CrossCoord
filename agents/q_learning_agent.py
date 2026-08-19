import numpy as np
import random
import os
import pickle

class QLearningAgent:
    """
    Q-Learning agent for Tier-3 executors.
    Learns collision avoidance and optimal pathfinding through
    interaction with the grid environment.
    
    State:  (row, col, goal_direction)
    Action: 0=UP, 1=RIGHT, 2=DOWN, 3=LEFT, 4=STAY
    """
    ACTIONS = {
        0: (-1, 0),   # UP
        1: (0, 1),    # RIGHT
        2: (1, 0),    # DOWN
        3: (0, -1),   # LEFT
        4: (0, 0),    # STAY
    }
    ACTION_NAMES = {0: "UP", 1: "RIGHT", 2: "DOWN", 3: "LEFT", 4: "STAY"}

    def __init__(self, agent_id, grid, learning_rate=0.1, discount=0.95,
                 epsilon=1.0, epsilon_decay=0.9995, epsilon_min=0.05):
        self.agent_id = agent_id
        self.grid = grid
        self.h, self.w = grid.shape
        self.lr = learning_rate
        self.gamma = discount
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min

        # Q-table: state -> action -> value
        # State is (row, col, goal_dir) where goal_dir encodes relative direction to goal
        self.q_table = {}

        # Training metrics
        self.episode_rewards = []
        self.episode_lengths = []

    def _get_state(self, pos, goal):
        """Encode state as (row, col, goal_quadrant)."""
        r, c = pos
        gr, gc = goal
        # Encode relative direction to goal as a quadrant (0-7 for 8 directions)
        dr = np.sign(gr - r)  # -1, 0, 1
        dc = np.sign(gc - c)  # -1, 0, 1
        goal_dir = (dr + 1) * 3 + (dc + 1)  # 0-8
        return (r, c, goal_dir)

    def _get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def _set_q(self, state, action, value):
        self.q_table[(state, action)] = value

    def choose_action(self, state, training=True):
        """Epsilon-greedy action selection."""
        if training and random.random() < self.epsilon:
            return random.randint(0, 4)

        # Exploit: pick best action
        q_values = [self._get_q(state, a) for a in range(5)]
        max_q = max(q_values)
        # Break ties randomly
        best_actions = [a for a in range(5) if q_values[a] == max_q]
        return random.choice(best_actions)

    def compute_reward(self, pos, new_pos, goal, hit_obstacle, hit_agent, reached_goal):
        """
        Reward shaping:
          +100  for reaching the goal
          -10   for hitting an obstacle
          -15   for colliding with another agent
          -0.1  step penalty (encourages shorter paths)
          +1    for moving closer to goal
          -1    for moving further from goal
        """
        if reached_goal:
            return 100.0
        if hit_obstacle:
            return -10.0
        if hit_agent:
            return -15.0

        # Distance-based shaping
        old_dist = abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])
        new_dist = abs(new_pos[0] - goal[0]) + abs(new_pos[1] - goal[1])

        reward = -0.1  # Step penalty
        if new_dist < old_dist:
            reward += 1.0
        elif new_dist > old_dist:
            reward -= 1.0

        return reward

    def train(self, start, goal, other_agent_positions=None, max_steps=500):
        """
        Train for one episode.
        Returns (total_reward, steps_taken, reached_goal).
        """
        pos = start
        total_reward = 0.0
        others = set(other_agent_positions or [])

        for step in range(max_steps):
            state = self._get_state(pos, goal)
            action = self.choose_action(state, training=True)

            dr, dc = self.ACTIONS[action]
            new_pos = (pos[0] + dr, pos[1] + dc)

            # Check boundaries
            hit_obstacle = False
            hit_agent = False
            reached_goal = False

            if (new_pos[0] < 0 or new_pos[0] >= self.h or
                new_pos[1] < 0 or new_pos[1] >= self.w):
                hit_obstacle = True
                new_pos = pos  # Stay in place
            elif self.grid[new_pos] == 1:
                hit_obstacle = True
                new_pos = pos
            elif new_pos in others:
                hit_agent = True
                new_pos = pos
            elif new_pos == goal:
                reached_goal = True

            reward = self.compute_reward(pos, new_pos, goal, hit_obstacle, hit_agent, reached_goal)
            total_reward += reward

            # Q-Learning update
            new_state = self._get_state(new_pos, goal)
            best_next = max(self._get_q(new_state, a) for a in range(5))
            old_q = self._get_q(state, action)
            new_q = old_q + self.lr * (reward + self.gamma * best_next - old_q)
            self._set_q(state, action, new_q)

            pos = new_pos

            if reached_goal:
                self.episode_rewards.append(total_reward)
                self.episode_lengths.append(step + 1)
                return total_reward, step + 1, True

        self.episode_rewards.append(total_reward)
        self.episode_lengths.append(max_steps)
        return total_reward, max_steps, False

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def get_learned_path(self, start, goal, max_steps=500):
        """
        Use the learned Q-table to navigate (no exploration).
        Returns the path as a list of positions.
        """
        pos = start
        path = [pos]
        visited = set()
        visited.add(pos)

        for _ in range(max_steps):
            if pos == goal:
                break
            state = self._get_state(pos, goal)
            action = self.choose_action(state, training=False)
            dr, dc = self.ACTIONS[action]
            new_pos = (pos[0] + dr, pos[1] + dc)

            # Validate move
            if (0 <= new_pos[0] < self.h and 0 <= new_pos[1] < self.w
                    and self.grid[new_pos] == 0 and new_pos not in visited):
                pos = new_pos
                path.append(pos)
                visited.add(pos)
            else:
                # If stuck, try other actions
                moved = False
                for alt_action in range(5):
                    if alt_action == action:
                        continue
                    dr2, dc2 = self.ACTIONS[alt_action]
                    alt_pos = (pos[0] + dr2, pos[1] + dc2)
                    if (0 <= alt_pos[0] < self.h and 0 <= alt_pos[1] < self.w
                            and self.grid[alt_pos] == 0 and alt_pos not in visited):
                        pos = alt_pos
                        path.append(pos)
                        visited.add(pos)
                        moved = True
                        break
                if not moved:
                    break  # Truly stuck

        return path

    def save(self, filepath):
        """Save Q-table to disk."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump({
                'q_table': self.q_table,
                'epsilon': self.epsilon,
                'episode_rewards': self.episode_rewards,
                'episode_lengths': self.episode_lengths,
            }, f)

    def load(self, filepath):
        """Load Q-table from disk."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.q_table = data['q_table']
            self.epsilon = data['epsilon']
            self.episode_rewards = data.get('episode_rewards', [])
            self.episode_lengths = data.get('episode_lengths', [])


def train_agent_on_map(map_file, agent_id="QL_Agent", episodes=2000, 
                       max_steps_per_episode=500, save_path=None):
    """
    Train a Q-Learning agent on a given map.
    """
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from env.grid_parser import GridParser

    grid, h, w = GridParser.parse_map(map_file)
    agent = QLearningAgent(agent_id, grid)

    safe_cells = list(zip(*np.where(grid == 0)))
    
    print(f"\n{'='*60}")
    print(f"  Q-Learning Training: {agent_id}")
    print(f"  Map: {map_file} ({h}x{w})")
    print(f"  Episodes: {episodes}")
    print(f"{'='*60}")

    successes = 0
    for ep in range(1, episodes + 1):
        # Random start and goal
        start = safe_cells[random.randint(0, len(safe_cells) - 1)]
        goal = safe_cells[random.randint(0, len(safe_cells) - 1)]
        while goal == start:
            goal = safe_cells[random.randint(0, len(safe_cells) - 1)]

        # Simulate other agents as random obstacles
        others = set()
        for _ in range(random.randint(1, 3)):
            other = safe_cells[random.randint(0, len(safe_cells) - 1)]
            if other != start and other != goal:
                others.add(other)

        reward, steps, reached = agent.train(start, goal, others, max_steps_per_episode)
        agent.decay_epsilon()

        if reached:
            successes += 1

        if ep % (episodes // 10) == 0:
            recent_rewards = agent.episode_rewards[-100:]
            recent_lengths = agent.episode_lengths[-100:]
            avg_r = sum(recent_rewards) / len(recent_rewards)
            avg_l = sum(recent_lengths) / len(recent_lengths)
            success_rate = successes / ep * 100
            print(f"  Episode {ep:5d}/{episodes} | "
                  f"Avg Reward: {avg_r:7.1f} | "
                  f"Avg Steps: {avg_l:6.1f} | "
                  f"Success: {success_rate:5.1f}% | "
                  f"ε: {agent.epsilon:.4f}")

    if save_path:
        agent.save(save_path)
        print(f"\n  Model saved to: {save_path}")

    print(f"  Q-table size: {len(agent.q_table)} entries")
    print(f"  Final success rate: {successes/episodes*100:.1f}%")

    return agent


if __name__ == "__main__":
    # Train on the disaster relief map (small, fast)
    agent = train_agent_on_map(
        map_file="../datasets/disaster_relief/random-32-32-20.map",
        agent_id="QL_DisasterRelief",
        episodes=3000,
        save_path="../models/ql_disaster_relief.pkl",
    )

    # Test the learned policy
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from env.grid_parser import GridParser

    grid, h, w = GridParser.parse_map("../datasets/disaster_relief/random-32-32-20.map")
    safe = list(zip(*np.where(grid == 0)))
    start, goal = safe[0], safe[-1]
    path = agent.get_learned_path(start, goal)
    print(f"\n  Test path from {start} to {goal}: {len(path)} steps, reached: {path[-1] == goal}")
