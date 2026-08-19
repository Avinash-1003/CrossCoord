# CrossCoord Simulation Datasets

This folder contains the environmental benchmarks and agent profile data required to simulate the Multi-Agent System (MAS) outlined in the CrossCoord / AutoHMA-LLM framework.

## 1. Environmental Maps (MovingAI Benchmark)

Since the agents operate in physical space (requiring Q-learning for collision avoidance and pathfinding), we utilize standard Multi-Agent Path Finding (MAPF) grid maps from the MovingAI lab.

- `logistics/Berlin_1_256.map`: Represents a dense urban/warehouse environment for Tier-3 Ground Logistics (UGV_Carrier).
- `search_and_rescue/Boston_0_256.map`: Represents a sprawling city block layout for Aerial Reconnaissance (UAV_Quad) and Ground Inspection.
- `disaster_relief/random-32-32-20.map`: Represents the **unseen Fourth Domain** with 20% random obstacles (rubble/debris) to evaluate the Transfer/Adaptation Module.

## 2. Agent Profiles

- `agent_profiles/agent_capabilities.csv`: Defines the heterogeneous nature of the swarm. It includes Tier-1 Cloud LLMs, Tier-2 Device Dispatchers, and Tier-3 Executing Agents (UAVs/UGVs). Crucially, the `failure_probability` column is used by the simulation to trigger the random agent dropouts needed to evaluate the **Self-Healing Coordination Module**.

## Usage in Simulation

To run the simulation environments, these maps can be loaded into standard Python multi-agent frameworks (such as PettingZoo or BenchMARL) by parsing the `.map` files into 2D NumPy occupancy grids. The Tier-1 and Tier-2 LLMs will read the text descriptions of these environments to decompose tasks before passing coordinate waypoints to the Tier-3 RL agents.
