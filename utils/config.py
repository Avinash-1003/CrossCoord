import yaml
import os

DEFAULT_CONFIG = {
    "project": {
        "name": "CrossCoord",
        "version": "1.0",
        "description": "Transferable, Self-Healing Coordination Framework for Heterogeneous Multi-Agent Systems",
    },
    "environments": {
        "logistics": {
            "map_file": "datasets/logistics/Berlin_1_256.map",
            "obstacle_density": 0.15,
            "description": "Dense urban warehouse environment",
        },
        "search_and_rescue": {
            "map_file": "datasets/search_and_rescue/Boston_0_256.map",
            "obstacle_density": 0.25,
            "description": "City block layout for SAR operations",
        },
        "disaster_relief": {
            "map_file": "datasets/disaster_relief/random-32-32-20.map",
            "obstacle_density": 0.20,
            "description": "Unseen fourth domain with random rubble",
            "hazards": ["flooding", "structural_collapse"],
        },
    },
    "agents": {
        "tier3": {
            "A_003": {"type": "UAV_Quad", "failure_prob": 0.15},
            "A_004": {"type": "UAV_Heavy", "failure_prob": 0.12},
            "A_005": {"type": "UGV_Scout", "failure_prob": 0.10},
            "A_006": {"type": "UGV_Carrier", "failure_prob": 0.08},
        },
    },
    "simulation": {
        "max_steps": 500,
        "failure_rate_base": 0.02,
        "failure_rate_high": 0.05,
        "random_seed": 42,
    },
    "q_learning": {
        "learning_rate": 0.1,
        "discount_factor": 0.95,
        "epsilon_start": 1.0,
        "epsilon_decay": 0.9995,
        "epsilon_min": 0.05,
        "episodes": 3000,
        "max_steps_per_episode": 500,
    },
    "output": {
        "results_dir": "results",
        "models_dir": "models",
        "figures_dir": "results/figures",
    },
}


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file, falling back to defaults."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
        # Deep merge with defaults
        config = _deep_merge(DEFAULT_CONFIG, user_config)
        return config
    else:
        return DEFAULT_CONFIG.copy()


def save_default_config(config_path="config.yaml"):
    """Save the default configuration to a YAML file."""
    with open(config_path, 'w') as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
    print(f"Default config saved to: {config_path}")


def _deep_merge(base, override):
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


if __name__ == "__main__":
    save_default_config()
