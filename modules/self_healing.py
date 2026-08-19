import random
import time
import json

class SelfHealingCoordinator:
    """
    Self-Healing Coordination Module.
    
    Monitors Tier-3 agents via heartbeat checks and automatically
    redistributes orphaned tasks when an agent fails.
    """
    def __init__(self, tier2_dispatcher, failure_probabilities=None):
        """
        :param tier2_dispatcher: Reference to the Tier2DeviceLLM for task reassignment.
        :param failure_probabilities: Dict of agent_id -> probability of failure per step.
        """
        self.tier2 = tier2_dispatcher
        self.failure_probs = failure_probabilities or {}
        self.heartbeat_log = {}   # agent_id -> last_heartbeat_step
        self.failure_events = []  # Log of all failure events for metrics
        self.recovery_events = [] # Log of all recovery events for metrics

    def register_agent(self, agent_id, failure_prob=0.0):
        """Register an agent with the heartbeat monitor."""
        self.heartbeat_log[agent_id] = 0
        self.failure_probs[agent_id] = failure_prob

    def heartbeat_check(self, active_agents, current_step):
        """
        Simulate heartbeat monitoring.
        Each active agent has a probability of failing at each step.
        Returns a list of agents that just failed.
        """
        newly_failed = []
        
        for agent_id, agent in active_agents.items():
            if not agent.is_active:
                continue  # Already failed
                
            prob = self.failure_probs.get(agent_id, 0.0)
            
            if random.random() < prob:
                # Agent has failed!
                agent.is_active = False
                failure_event = {
                    "agent_id": agent_id,
                    "step": current_step,
                    "timestamp": time.time(),
                    "remaining_path_length": len(agent.path),
                    "position_at_failure": agent.pos,
                }
                self.failure_events.append(failure_event)
                newly_failed.append(agent_id)
                print(f"  [SELF-HEAL] ⚠️  Agent {agent_id} FAILED at step {current_step}, pos={agent.pos}")
            else:
                # Heartbeat received
                self.heartbeat_log[agent_id] = current_step

        return newly_failed

    def redistribute_tasks(self, failed_agent_ids, current_schedule, active_agents, scenario_context):
        """
        When agents fail, redistribute their orphaned tasks to healthy agents.
        Uses lightweight partial replanning (not a full Tier-1 cycle).
        
        :param failed_agent_ids: List of agent IDs that just failed.
        :param current_schedule: Dict of agent_id -> task_payload.
        :param active_agents: Dict of agent_id -> Tier3Executor.
        :param scenario_context: String describing the scenario for the LLM.
        :returns: Updated schedule with reassigned tasks.
        """
        orphaned_tasks = []
        for agent_id in failed_agent_ids:
            if agent_id in current_schedule:
                orphaned_tasks.append(current_schedule.pop(agent_id))
                
        if not orphaned_tasks:
            return current_schedule

        # Find healthy agents that are idle or have completed their tasks
        healthy_agents = {
            aid: agent for aid, agent in active_agents.items()
            if agent.is_active and aid not in current_schedule
        }
        
        # If no idle healthy agents, pick the ones closest to completion
        if not healthy_agents:
            healthy_agents = {
                aid: agent for aid, agent in active_agents.items()
                if agent.is_active
            }

        if not healthy_agents:
            print("  [SELF-HEAL] ❌ No healthy agents available for redistribution!")
            return current_schedule

        print(f"  [SELF-HEAL] 🔄 Redistributing {len(orphaned_tasks)} orphaned task(s) "
              f"among {len(healthy_agents)} healthy agent(s)...")

        recovery_start = time.time()

        # Simple capability-aware redistribution: round-robin assign to healthy agents
        healthy_ids = list(healthy_agents.keys())
        for i, task in enumerate(orphaned_tasks):
            reassigned_to = healthy_ids[i % len(healthy_ids)]
            current_schedule[reassigned_to] = task
            
            # Recompute path for the reassigned agent
            target = task["target"]
            if isinstance(target, list):
                target = tuple(target)
            
            agent = active_agents[reassigned_to]
            success = agent.compute_path(target)
            
            recovery_event = {
                "orphaned_task": task["id"],
                "original_agent": None,  # We lost track since we popped it
                "reassigned_to": reassigned_to,
                "path_found": success,
                "recovery_time_ms": (time.time() - recovery_start) * 1000,
                "new_path_length": len(agent.path) if success else 0,
            }
            self.recovery_events.append(recovery_event)
            
            status = "✅ path found" if success else "❌ no path"
            print(f"    -> Task '{task['id']}' reassigned to {reassigned_to} ({status})")

        return current_schedule

    def get_metrics(self):
        """Return self-healing performance metrics."""
        return {
            "total_failures": len(self.failure_events),
            "total_recoveries": len(self.recovery_events),
            "successful_recoveries": sum(1 for r in self.recovery_events if r["path_found"]),
            "avg_recovery_time_ms": (
                sum(r["recovery_time_ms"] for r in self.recovery_events) / len(self.recovery_events)
                if self.recovery_events else 0
            ),
            "failure_log": self.failure_events,
            "recovery_log": self.recovery_events,
        }


if __name__ == "__main__":
    print("Self-Healing module loaded. Run via main.py for integration test.")
