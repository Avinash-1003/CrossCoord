import json
import copy

class TransferAdaptationModule:
    """
    Transfer/Adaptation Module.

    Separates domain-general coordination knowledge from domain-specific
    knowledge, enabling zero-shot or few-shot transfer to unseen domains.

    Domain-General Knowledge (frozen, reused):
        - Task decomposition patterns (split complex missions into subtasks)
        - Role assignment heuristics (match agent type to task type)
        - Communication protocols (how tiers exchange messages)
        - Failure-recovery procedures (self-healing workflow)

    Domain-Specific Knowledge (retrained per domain):
        - Map/environment layout and obstacle distribution
        - Agent starting positions and safe zones
        - Domain-specific task targets and success criteria
        - Environmental hazards unique to the domain
    """

    def __init__(self):
        # Domain-general knowledge store (shared across all domains)
        self.general_knowledge = {
            "decomposition_rules": [
                "Split a mission into independent subtasks that can run in parallel.",
                "Match each subtask type to the most capable agent type.",
                "Prioritize safety-critical tasks (rescue > logistics > inspection).",
            ],
            "role_mapping": {
                "Aerial_Reconnaissance": ["UAV_Quad", "UAV_Heavy"],
                "Aerial_Logistics": ["UAV_Heavy"],
                "Ground_Inspection": ["UGV_Scout"],
                "Ground_Logistics": ["UGV_Carrier"],
                "Environment_Monitoring": ["Static_Sensor"],
            },
            "communication_protocol": {
                "tier1_to_tier2": "JSON subtask list",
                "tier2_to_tier3": "Waypoint coordinates + task ID",
                "tier3_to_tier2": "Status heartbeat (position, battery, task %)",
            },
            "recovery_protocol": {
                "detection": "Heartbeat timeout > 3 consecutive misses",
                "action": "Redistribute orphaned task via capability matching",
                "fallback": "Escalate to Tier-1 for full replan if >50% agents fail",
            },
        }

        # Domain-specific adapter stores (one per domain)
        self.domain_adapters = {}

        # Metrics
        self.transfer_log = []

    def register_domain(self, domain_name, domain_config):
        """
        Register a new domain-specific adapter.
        :param domain_name: e.g., "logistics", "search_and_rescue", "disaster_relief"
        :param domain_config: Dict with domain-specific parameters.
        """
        self.domain_adapters[domain_name] = {
            "name": domain_name,
            "map_file": domain_config.get("map_file", ""),
            "grid_size": domain_config.get("grid_size", (0, 0)),
            "obstacle_density": domain_config.get("obstacle_density", 0.0),
            "agent_start_positions": domain_config.get("agent_start_positions", {}),
            "task_targets": domain_config.get("task_targets", []),
            "hazards": domain_config.get("hazards", []),
            "success_criteria": domain_config.get("success_criteria", "All tasks completed"),
        }
        print(f"[Transfer] Registered domain adapter: '{domain_name}'")

    def transfer_to_domain(self, target_domain_name, target_domain_config=None):
        """
        Prepare to operate in a new (potentially unseen) domain.

        If we have a pre-trained adapter for this domain, use it directly.
        If not, create a minimal adapter from the config (zero-shot transfer)
        by reusing all domain-general knowledge and only adapting the
        domain-specific layer.

        :returns: Combined knowledge bundle for this domain.
        """
        if target_domain_name in self.domain_adapters:
            print(f"[Transfer] ✅ Known domain '{target_domain_name}' — using existing adapter.")
            adapter = self.domain_adapters[target_domain_name]
            transfer_type = "known"
        elif target_domain_config:
            print(f"[Transfer] 🔄 Unseen domain '{target_domain_name}' — creating zero-shot adapter.")
            self.register_domain(target_domain_name, target_domain_config)
            adapter = self.domain_adapters[target_domain_name]
            transfer_type = "zero_shot"
        else:
            print(f"[Transfer] ❌ Unknown domain '{target_domain_name}' and no config provided.")
            return None

        # Build the combined knowledge bundle
        bundle = {
            "general": copy.deepcopy(self.general_knowledge),
            "specific": copy.deepcopy(adapter),
            "transfer_type": transfer_type,
        }

        self.transfer_log.append({
            "domain": target_domain_name,
            "transfer_type": transfer_type,
            "general_rules_count": len(self.general_knowledge["decomposition_rules"]),
            "specific_params_count": len(adapter),
        })

        return bundle

    def get_role_for_task(self, task_type):
        """
        Use domain-general role mapping to find suitable agent types for a task.
        """
        return self.general_knowledge["role_mapping"].get(task_type, [])

    def get_metrics(self):
        """Return transfer/adaptation performance metrics."""
        known_transfers = sum(1 for t in self.transfer_log if t["transfer_type"] == "known")
        zero_shot_transfers = sum(1 for t in self.transfer_log if t["transfer_type"] == "zero_shot")
        return {
            "total_transfers": len(self.transfer_log),
            "known_domain_transfers": known_transfers,
            "zero_shot_transfers": zero_shot_transfers,
            "registered_domains": list(self.domain_adapters.keys()),
            "transfer_log": self.transfer_log,
        }


if __name__ == "__main__":
    tam = TransferAdaptationModule()

    # Register known domains (the 3 from AutoHMA-LLM)
    tam.register_domain("logistics", {
        "map_file": "datasets/logistics/Berlin_1_256.map",
        "grid_size": (256, 256),
        "obstacle_density": 0.15,
        "task_targets": [(15, 20), (5, 5)],
    })
    tam.register_domain("search_and_rescue", {
        "map_file": "datasets/search_and_rescue/Boston_0_256.map",
        "grid_size": (256, 256),
        "obstacle_density": 0.25,
        "task_targets": [(50, 50), (100, 100)],
    })

    # Transfer to a known domain
    bundle_known = tam.transfer_to_domain("logistics")
    print(f"  Transfer type: {bundle_known['transfer_type']}")

    # Transfer to an UNSEEN domain (zero-shot)
    bundle_new = tam.transfer_to_domain("disaster_relief", {
        "map_file": "datasets/disaster_relief/random-32-32-20.map",
        "grid_size": (32, 32),
        "obstacle_density": 0.20,
        "task_targets": [(31, 31), (10, 10)],
        "hazards": ["flooding", "structural_collapse"],
    })
    print(f"  Transfer type: {bundle_new['transfer_type']}")

    print("\nMetrics:", json.dumps(tam.get_metrics(), indent=2))
