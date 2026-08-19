import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import os

class Visualizer:
    """
    Visualization engine for CrossCoord simulations.
    Generates publication-quality figures for evaluation reports.
    """
    COLORS = {
        'obstacle': '#2C3E50',
        'passable': '#ECF0F1',
        'UAV_Quad': '#E74C3C',
        'UAV_Heavy': '#E67E22',
        'UGV_Scout': '#2ECC71',
        'UGV_Carrier': '#3498DB',
        'goal': '#9B59B6',
        'path': '#F1C40F',
        'failed': '#95A5A6',
    }

    @staticmethod
    def render_grid_snapshot(grid, agents, goals, paths=None, title="CrossCoord Simulation",
                             save_path=None, step_num=None):
        """
        Render a single snapshot of the grid environment.
        :param grid: 2D numpy array
        :param agents: dict of {agent_id: (row, col, agent_type, is_active)}
        :param goals: dict of {agent_id: (row, col)}
        :param paths: dict of {agent_id: [(r,c), ...]}
        """
        h, w = grid.shape
        fig_size = max(6, min(14, w / 20))
        fig, ax = plt.subplots(1, 1, figsize=(fig_size, fig_size))

        # Draw grid
        display = np.zeros((h, w, 3))
        for r in range(h):
            for c in range(w):
                if grid[r, c] == 1:
                    display[r, c] = [0.173, 0.243, 0.314]  # obstacle
                else:
                    display[r, c] = [0.926, 0.941, 0.945]  # passable

        ax.imshow(display, interpolation='nearest')

        # Draw paths
        if paths:
            for aid, path in paths.items():
                if not path:
                    continue
                color = Visualizer.COLORS.get(
                    agents.get(aid, (0, 0, 'UAV_Quad', True))[2], '#F1C40F'
                )
                pr = [p[0] for p in path]
                pc = [p[1] for p in path]
                ax.plot(pc, pr, '-', color=color, alpha=0.4, linewidth=1.5)

        # Draw goals
        for aid, (gr, gc) in goals.items():
            ax.plot(gc, gr, '*', color=Visualizer.COLORS['goal'],
                    markersize=12, markeredgecolor='white', markeredgewidth=0.8)

        # Draw agents
        legend_handles = []
        drawn_types = set()
        for aid, (ar, ac, atype, active) in agents.items():
            color = Visualizer.COLORS.get(atype, '#3498DB')
            if not active:
                color = Visualizer.COLORS['failed']
                marker = 'X'
            else:
                marker = 'o'

            ax.plot(ac, ar, marker, color=color, markersize=10,
                    markeredgecolor='white', markeredgewidth=1.2)
            ax.annotate(aid[-3:], (ac, ar), fontsize=6, ha='center',
                        va='bottom', color='white',
                        bbox=dict(boxstyle='round,pad=0.15', fc=color, alpha=0.85))

            if atype not in drawn_types:
                drawn_types.add(atype)
                label = f"{atype}" + (" (failed)" if not active else "")
                legend_handles.append(
                    mpatches.Patch(color=color, label=label)
                )

        legend_handles.append(
            plt.Line2D([0], [0], marker='*', color='w',
                       markerfacecolor=Visualizer.COLORS['goal'],
                       markersize=10, label='Goal')
        )

        ax.legend(handles=legend_handles, loc='upper right', fontsize=7,
                  facecolor='white', edgecolor='gray', framealpha=0.9)

        title_text = title
        if step_num is not None:
            title_text += f" (Step {step_num})"
        ax.set_title(title_text, fontsize=12, fontweight='bold', pad=10)
        ax.set_xlabel('Column')
        ax.set_ylabel('Row')
        ax.grid(True, alpha=0.15, linewidth=0.3)

        plt.tight_layout()
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"  [Viz] Saved snapshot: {save_path}")
        plt.close()

    @staticmethod
    def plot_training_curves(episode_rewards, episode_lengths, agent_id,
                             save_path=None, window=100):
        """Plot Q-Learning training reward and episode length curves."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        # Smoothed rewards
        ax = axes[0]
        ax.plot(episode_rewards, alpha=0.2, color='#3498DB')
        if len(episode_rewards) >= window:
            smoothed = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
            ax.plot(range(window-1, len(episode_rewards)), smoothed,
                    color='#2C3E50', linewidth=2, label=f'{window}-ep avg')
        ax.set_title(f'Training Rewards — {agent_id}', fontweight='bold')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Total Reward')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Smoothed episode lengths
        ax = axes[1]
        ax.plot(episode_lengths, alpha=0.2, color='#E74C3C')
        if len(episode_lengths) >= window:
            smoothed = np.convolve(episode_lengths, np.ones(window)/window, mode='valid')
            ax.plot(range(window-1, len(episode_lengths)), smoothed,
                    color='#2C3E50', linewidth=2, label=f'{window}-ep avg')
        ax.set_title(f'Episode Length — {agent_id}', fontweight='bold')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Steps')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"  [Viz] Saved training curves: {save_path}")
        plt.close()

    @staticmethod
    def plot_benchmark_comparison(results, metric_key, title, ylabel,
                                  save_path=None):
        """
        Bar chart comparing a metric across multiple scenarios.
        :param results: dict of {scenario_name: metrics_report}
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        scenarios = list(results.keys())
        values = []
        for s in scenarios:
            report = results[s]
            # Navigate nested keys like "task_accuracy.accuracy_pct"
            keys = metric_key.split('.')
            val = report
            for k in keys:
                val = val[k]
            values.append(val)

        colors = ['#3498DB', '#E74C3C', '#2ECC71', '#E67E22', '#9B59B6']
        bars = ax.bar(scenarios, values, color=colors[:len(scenarios)],
                      edgecolor='white', linewidth=1.5)

        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=11)

        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_xlabel('Scenario', fontsize=12)
        ax.grid(True, axis='y', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"  [Viz] Saved benchmark chart: {save_path}")
        plt.close()

    @staticmethod
    def plot_self_healing_timeline(failure_events, recovery_events, 
                                   total_steps, save_path=None):
        """Plot a timeline of agent failures and recoveries."""
        fig, ax = plt.subplots(figsize=(12, 4))

        # Plot failure events
        for fe in failure_events:
            ax.axvline(x=fe['step'], color='#E74C3C', linestyle='--',
                       alpha=0.7, linewidth=1.5)
            ax.annotate(f"⚠ {fe['agent_id']}", (fe['step'], 0.8),
                        fontsize=8, color='#E74C3C', rotation=45,
                        ha='left', va='bottom')

        # Plot recovery events
        for i, re in enumerate(recovery_events):
            color = '#2ECC71' if re['path_found'] else '#E67E22'
            label = f"→ {re['reassigned_to']}"
            ax.annotate(label, (failure_events[min(i, len(failure_events)-1)]['step'], 0.4),
                        fontsize=7, color=color)

        ax.set_xlim(0, total_steps)
        ax.set_ylim(0, 1)
        ax.set_xlabel('Simulation Step', fontsize=12)
        ax.set_title('Self-Healing Timeline: Failures & Recoveries',
                     fontsize=13, fontweight='bold')
        ax.set_yticks([])
        ax.grid(True, axis='x', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

        # Legend
        ax.plot([], [], '--', color='#E74C3C', label='Agent Failure')
        ax.plot([], [], 's', color='#2ECC71', label='Successful Recovery')
        ax.legend(loc='upper right', fontsize=9)

        plt.tight_layout()
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"  [Viz] Saved self-healing timeline: {save_path}")
        plt.close()

    @staticmethod
    def plot_transfer_comparison(results, save_path=None):
        """
        Radar chart comparing known vs zero-shot domain performance.
        """
        categories = ['Task Accuracy\n(%)', 'Recovery Rate\n(%)',
                       'Comm. Efficiency\n(inv. calls)', 'Adaptation\nSpeed']
        N = len(categories)

        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        for scenario, report in results.items():
            ta = report['task_accuracy']['accuracy_pct']
            sh = report.get('self_healing', {})
            recoveries = sh.get('total_recoveries', 0)
            failures = sh.get('total_failures', 1)
            recovery_rate = (sh.get('successful_recoveries', 0) / max(recoveries, 1)) * 100
            comm_eff = max(0, 100 - report['communication_overhead']['total_llm_calls'] * 10)
            
            transfer = report.get('transfer_adaptation', {})
            adapt_speed = 100 if transfer.get('zero_shot_transfers', 0) > 0 else 80

            values = [ta, recovery_rate, comm_eff, adapt_speed]
            values += values[:1]

            ax.plot(angles, values, 'o-', linewidth=2, label=scenario)
            ax.fill(angles, values, alpha=0.15)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_ylim(0, 110)
        ax.set_title('CrossCoord Performance Radar', fontsize=14,
                     fontweight='bold', pad=20)
        ax.legend(loc='lower right', bbox_to_anchor=(1.3, 0), fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"  [Viz] Saved radar chart: {save_path}")
        plt.close()


if __name__ == "__main__":
    print("Visualizer module loaded. Use from main.py or benchmark.py.")
