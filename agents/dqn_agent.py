import os
import random
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque, namedtuple

# ----------------- REPLAY BUFFER -----------------
Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward', 'done'))

class ReplayBuffer:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)

    def push(self, *args):
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)

# ----------------- NEURAL NETWORK -----------------
class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(DQN, self).__init__()
        # Deeper network than standard linear regression
        self.fc1 = nn.Linear(input_dim, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, 64)
        self.out = nn.Linear(64, output_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        return self.out(x)

# ----------------- DQN AGENT -----------------
class DQNAgent:
    """
    Deep Q-Network Agent for Tier-3 executors using PyTorch.
    Replaces tabular Q-Learning to prove advanced DRL competency.
    """
    ACTIONS = {
        0: (-1, 0),   # UP
        1: (0, 1),    # RIGHT
        2: (1, 0),    # DOWN
        3: (0, -1),   # LEFT
        4: (0, 0),    # STAY
    }

    def __init__(self, agent_id, grid, lr=1e-3, gamma=0.99, 
                 epsilon_start=1.0, epsilon_end=0.05, epsilon_decay=0.995,
                 batch_size=64, memory_size=100000):
        self.agent_id = agent_id
        self.grid = grid
        self.h, self.w = grid.shape
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        
        # State: [r/h, c/w, goal_r/h, goal_c/w]
        self.state_dim = 4
        self.action_dim = 5
        
        # Device configuration
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")

        # Networks
        self.policy_net = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_net = DQN(self.state_dim, self.action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.memory = ReplayBuffer(memory_size)
        
        # Metrics
        self.episode_rewards = []
        self.episode_lengths = []

    def _get_state(self, pos, goal):
        """Normalize coordinates for neural network."""
        return np.array([
            pos[0] / self.h, 
            pos[1] / self.w, 
            goal[0] / self.h, 
            goal[1] / self.w
        ], dtype=np.float32)

    def choose_action(self, state, training=True):
        """Epsilon-greedy with neural network."""
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
            
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()

    def optimize_model(self):
        """Sample from buffer and perform one step of gradient descent."""
        if len(self.memory) < self.batch_size:
            return
            
        transitions = self.memory.sample(self.batch_size)
        batch = Transition(*zip(*transitions))
        
        state_batch = torch.FloatTensor(np.array(batch.state)).to(self.device)
        action_batch = torch.LongTensor(batch.action).unsqueeze(1).to(self.device)
        reward_batch = torch.FloatTensor(batch.reward).to(self.device)
        next_state_batch = torch.FloatTensor(np.array(batch.next_state)).to(self.device)
        done_batch = torch.FloatTensor(batch.done).to(self.device)
        
        # Compute Q(s_t, a)
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)
        
        # Compute V(s_{t+1}) for all next states
        with torch.no_grad():
            next_state_values = self.target_net(next_state_batch).max(1)[0]
            
        # Compute expected Q values
        expected_state_action_values = reward_batch + (self.gamma * next_state_values * (1 - done_batch))
        
        # Compute Huber loss
        criterion = nn.SmoothL1Loss()
        loss = criterion(state_action_values, expected_state_action_values.unsqueeze(1))
        
        # Optimize the model
        self.optimizer.zero_grad()
        loss.backward()
        # In-place gradient clipping
        torch.nn.utils.clip_grad_value_(self.policy_net.parameters(), 100)
        self.optimizer.step()

    def compute_reward(self, pos, new_pos, goal, hit_obstacle, hit_agent, reached_goal):
        if reached_goal:
            return 100.0
        if hit_obstacle:
            return -10.0
        if hit_agent:
            return -20.0
            
        # Distance-based dense reward
        old_dist = abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])
        new_dist = abs(new_pos[0] - goal[0]) + abs(new_pos[1] - goal[1])
        
        reward = -0.5  # Step penalty
        if new_dist < old_dist:
            reward += 2.0
        elif new_dist > old_dist:
            reward -= 2.0
            
        return reward

    def train(self, start, goal, other_agent_positions=None, max_steps=500):
        pos = start
        total_reward = 0.0
        others = set(other_agent_positions or [])
        
        state = self._get_state(pos, goal)
        
        for step in range(max_steps):
            action = self.choose_action(state, training=True)
            
            dr, dc = self.ACTIONS[action]
            new_pos = (pos[0] + dr, pos[1] + dc)
            
            hit_obstacle = False
            hit_agent = False
            reached_goal = False
            
            if (new_pos[0] < 0 or new_pos[0] >= self.h or
                new_pos[1] < 0 or new_pos[1] >= self.w):
                hit_obstacle = True
                new_pos = pos
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
            done = reached_goal
            
            next_state = self._get_state(new_pos, goal)
            
            # Store in memory
            self.memory.push(state, action, next_state, reward, done)
            
            # Perform one step of optimization
            self.optimize_model()
            
            state = next_state
            pos = new_pos
            
            if done:
                self.episode_rewards.append(total_reward)
                self.episode_lengths.append(step + 1)
                return total_reward, step + 1, True
                
        self.episode_rewards.append(total_reward)
        self.episode_lengths.append(max_steps)
        return total_reward, max_steps, False

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        torch.save(self.policy_net.state_dict(), filepath)
        
    def load(self, filepath):
        if os.path.exists(filepath):
            self.policy_net.load_state_dict(torch.load(filepath, map_location=self.device))
            self.target_net.load_state_dict(self.policy_net.state_dict())
            self.policy_net.eval()
            self.target_net.eval()


def train_dqn_agent(map_file, agent_id="DQN_Agent", episodes=500, save_path=None):
    """Training loop for the Deep Q-Network Agent."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from env.grid_parser import GridParser

    grid, h, w = GridParser.parse_map(map_file)
    agent = DQNAgent(agent_id, grid)

    safe_cells = list(zip(*np.where(grid == 0)))
    
    print(f"\n{'='*60}")
    print(f"  PyTorch DRL Training: {agent_id}")
    print(f"  Map: {map_file} ({h}x{w})")
    print(f"  Device: {agent.device}")
    print(f"{'='*60}")

    successes = 0
    TARGET_UPDATE = 10
    
    for ep in range(1, episodes + 1):
        start = safe_cells[random.randint(0, len(safe_cells) - 1)]
        goal = safe_cells[random.randint(0, len(safe_cells) - 1)]
        while goal == start:
            goal = safe_cells[random.randint(0, len(safe_cells) - 1)]

        reward, steps, reached = agent.train(start, goal, max_steps=200)
        agent.decay_epsilon()
        
        if ep % TARGET_UPDATE == 0:
            agent.update_target_network()

        if reached:
            successes += 1

        if ep % max(1, episodes // 10) == 0:
            recent_rewards = agent.episode_rewards[-50:]
            avg_r = sum(recent_rewards) / len(recent_rewards)
            print(f"  Episode {ep:4d}/{episodes} | Avg Reward: {avg_r:7.1f} | ε: {agent.epsilon:.3f}")

    if save_path:
        agent.save(save_path)
        print(f"\n  PyTorch Model saved to: {save_path}")

    return agent

if __name__ == "__main__":
    train_dqn_agent(
        map_file="../datasets/disaster_relief/random-32-32-20.map",
        episodes=300,
        save_path="../models/dqn_disaster_relief.pth"
    )
