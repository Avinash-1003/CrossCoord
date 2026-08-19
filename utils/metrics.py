import time
import json

class MetricsTracker:
    """
    Tracks and computes all evaluation metrics for CrossCoord.
    """
    def __init__(self):
        self.mission_start_time = None
        self.mission_end_time = None
        self.total_steps = 0
        self.tasks_assigned = 0
        self.tasks_completed = 0
        self.llm_calls = 0          # Communication overhead proxy
        self.agent_steps = {}       # agent_id -> number of steps taken

    def start_mission(self):
        self.mission_start_time = time.time()

    def end_mission(self):
        self.mission_end_time = time.time()

    def log_llm_call(self):
        self.llm_calls += 1

    def log_task_assigned(self):
        self.tasks_assigned += 1

    def log_task_completed(self, agent_id):
        self.tasks_completed += 1

    def log_agent_step(self, agent_id):
        self.agent_steps[agent_id] = self.agent_steps.get(agent_id, 0) + 1
        self.total_steps += 1

    def compute_report(self, self_healing_metrics=None, transfer_metrics=None):
        """
        Generate a full evaluation report.
        """
        elapsed = (self.mission_end_time - self.mission_start_time) if self.mission_end_time else 0

        report = {
            "mission_duration_sec": round(elapsed, 4),
            "total_simulation_steps": self.total_steps,
            "task_accuracy": {
                "assigned": self.tasks_assigned,
                "completed": self.tasks_completed,
                "accuracy_pct": round(
                    (self.tasks_completed / self.tasks_assigned * 100)
                    if self.tasks_assigned > 0 else 0, 2
                ),
            },
            "communication_overhead": {
                "total_llm_calls": self.llm_calls,
            },
            "per_agent_steps": self.agent_steps,
        }

        if self_healing_metrics:
            report["self_healing"] = self_healing_metrics

        if transfer_metrics:
            report["transfer_adaptation"] = transfer_metrics

        return report

    def print_report(self, report):
        """Pretty-print the evaluation report."""
        print("\n" + "=" * 60)
        print("         CROSSCOORD EVALUATION REPORT")
        print("=" * 60)
        print(f"  Mission Duration:      {report['mission_duration_sec']} sec")
        print(f"  Total Sim Steps:       {report['total_simulation_steps']}")
        print(f"  Tasks Assigned:        {report['task_accuracy']['assigned']}")
        print(f"  Tasks Completed:       {report['task_accuracy']['completed']}")
        print(f"  Task Accuracy:         {report['task_accuracy']['accuracy_pct']}%")
        print(f"  LLM Calls (Overhead):  {report['communication_overhead']['total_llm_calls']}")

        if "self_healing" in report:
            sh = report["self_healing"]
            print(f"\n  --- Self-Healing ---")
            print(f"  Total Failures:        {sh['total_failures']}")
            print(f"  Total Recoveries:      {sh['total_recoveries']}")
            print(f"  Successful Recoveries: {sh['successful_recoveries']}")
            print(f"  Avg Recovery Time:     {sh['avg_recovery_time_ms']:.2f} ms")

        if "transfer_adaptation" in report:
            ta = report["transfer_adaptation"]
            print(f"\n  --- Transfer/Adaptation ---")
            print(f"  Total Transfers:       {ta['total_transfers']}")
            print(f"  Known Domain:          {ta['known_domain_transfers']}")
            print(f"  Zero-Shot Transfers:   {ta['zero_shot_transfers']}")
            print(f"  Registered Domains:    {ta['registered_domains']}")

        print("=" * 60)
