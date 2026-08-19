# CrossCoord

**A Transferable, Self-Healing Coordination Framework for Heterogeneous Multi-Agent Systems Across Unseen Operational Domains**

> Extends the AutoHMA-LLM architecture (Yang et al., IEEE TCCN, 2025) with cross-domain transfer learning and real-time agent failure recovery.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    TIER 1 — CLOUD LLM                        │
│              (Central Planner / Task Decomposer)             │
│    ┌─────────────────────────────────────────────────────┐   │
│    │  Transfer/Adaptation Module                         │   │
│    │  ├── Domain-General Knowledge (frozen)              │   │
│    │  └── Domain-Specific Adapters (per environment)     │   │
│    └─────────────────────────────────────────────────────┘   │
└──────────────┬───────────────────────────┬───────────────────┘
               │ Subtask Plans             │ Subtask Plans
       ┌───────▼──────────┐        ┌───────▼──────────┐
       │  TIER 2 — DEVICE │        │  TIER 2 — DEVICE │
       │  LLM Dispatcher  │        │  LLM Dispatcher  │
       │  ┌─────────────┐ │        │  ┌─────────────┐ │
       │  │ Self-Healing │ │        │  │ Self-Healing │ │
       │  │ Heartbeat    │ │        │  │ Heartbeat    │ │
       │  │ Monitor      │ │        │  │ Monitor      │ │
       │  └─────────────┘ │        │  └─────────────┘ │
       └──┬────┬────┬─────┘        └──┬────┬────┬─────┘
          │    │    │                  │    │    │
       ┌──▼┐┌─▼─┐┌─▼─┐            ┌──▼┐┌─▼─┐┌─▼─┐
       │UAV││UGV ││UAV│            │UGV││UAV ││UGV│
       │   ││    ││   │            │   ││    ││   │
       │T3 ││T3  ││T3 │            │T3 ││T3  ││T3 │
       └───┘└────┘└───┘            └───┘└────┘└───┘
        TIER 3 — Generative Agents (Q-Learning + A*)
```

## Project Structure

```
CrossCoord/
├── main.py                  # Single-mission runner
├── benchmark.py             # Full benchmark suite with plots
├── config.yaml              # Configuration file
├── env/
│   ├── grid_parser.py       # MovingAI .map → NumPy loader
│   └── simulation_env.py    # 2D grid simulation engine
├── agents/
│   ├── tier1_cloud_llm.py   # Tier-1 Central Planner
│   ├── tier2_device_llm.py  # Tier-2 Dispatcher
│   ├── tier3_executor.py    # Tier-3 Physical agents (A*)
│   └── q_learning_agent.py  # Q-Learning RL agent with collision avoidance
├── modules/
│   ├── self_healing.py      # Heartbeat monitor + task redistribution
│   └── transfer_adaptation.py  # Domain-general/specific knowledge split
├── utils/
│   ├── mock_llm.py          # Mock LLM for local testing
│   ├── metrics.py           # Evaluation metrics tracker
│   ├── visualizer.py        # Publication-quality plots
│   └── config.py            # YAML configuration loader
├── datasets/
│   ├── logistics/           # Berlin warehouse maps
│   ├── search_and_rescue/   # Boston city maps
│   ├── disaster_relief/     # Unseen fourth domain maps
│   └── agent_profiles/      # Agent capability CSV
├── models/                  # Saved Q-table models
└── results/                 # Benchmark outputs and figures
```

## Quick Start

```bash
# Run a single mission
python3 main.py

# Run the full benchmark suite (trains RL, runs all scenarios, generates plots)
python3 benchmark.py
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Tier LLM Architecture** | Cloud LLM → Device LLM → Generative Agents |
| **Q-Learning Collision Avoidance** | RL-trained pathfinding with multi-agent awareness |
| **Transfer/Adaptation Module** | Zero-shot transfer to unseen domains via knowledge separation |
| **Self-Healing Coordination** | Heartbeat monitoring + automatic task redistribution |
| **Benchmark Suite** | Systematic evaluation across domains and failure rates |
| **Visualization Engine** | Grid snapshots, training curves, radar charts, timelines |

## Evaluation Metrics

- **Task Completion Accuracy** — % of assigned tasks successfully completed
- **Communication Overhead** — Total LLM API calls during a mission
- **Retraining Cost** — Zero-shot vs known domain adaptation
- **Recovery Time** — Time from agent failure to resumed coordination
- **Task-Completion Resilience** — Accuracy under 0%, 2%, 5% agent dropout rates

## Dependencies

```bash
pip install numpy matplotlib pyyaml
```

## Authors

- *[Your Names]*
- Department of IT, CBIT
- Under the guidance of *[Supervisor Name]*
