import streamlit as st
import time
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
from io import BytesIO

# Fix path to import CrossCoord modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env.grid_parser import GridParser
from env.simulation_env import CrossCoordEnv
from agents.tier1_cloud_llm import Tier1CloudLLM
from agents.tier2_device_llm import Tier2DeviceLLM
from agents.tier3_executor import Tier3Executor
from modules.self_healing import SelfHealingCoordinator
from modules.transfer_adaptation import TransferAdaptationModule
from utils.llm_client import CrossCoordLLM
from utils.visualizer import Visualizer

# --- CONFIGURATION ---
st.set_page_config(page_title="CrossCoord Dashboard", layout="wide", page_icon="🚁")

st.title("🚁 CrossCoord: Live Simulation Dashboard")
st.markdown("Transferable, Self-Healing Coordination Framework for Heterogeneous Multi-Agent Systems")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Simulation Settings")
    
    domain_choice = st.selectbox("Select Domain", [
        "disaster_relief", "logistics", "search_and_rescue"
    ])
    
    failure_rate = st.slider("Agent Failure Rate (%)", 0, 20, 2) / 100.0
    
    sim_speed = st.slider("Simulation Speed (ms per step)", 10, 500, 100)
    
    st.divider()
    
    st.header("🧠 AI Backend")
    api_key = st.text_input("OpenAI API Key (Optional)", type="password")
    use_real_llm = st.checkbox("Use Real GPT-4o-mini", value=False)
    
    if use_real_llm and not api_key:
        st.warning("Please enter an API key to use real LLM, otherwise MockLLM will be used.")

    st.divider()
    
    start_btn = st.button("🚀 Start Simulation", use_container_width=True)

# --- MAPS ---
MAP_FILES = {
    "disaster_relief": "datasets/disaster_relief/random-32-32-20.map",
    "logistics": "datasets/logistics/Berlin_1_256.map",
    "search_and_rescue": "datasets/search_and_rescue/Boston_0_256.map",
}

# --- SIMULATION LOGIC ---
def render_frame(grid, tier3_agents, schedule, step):
    """Render the grid as an image buffer for Streamlit."""
    agents_state = {}
    paths_state = {}
    for aid, agent in tier3_agents.items():
        agents_state[aid] = (agent.pos[0], agent.pos[1], agent.agent_type, agent.is_active)
        paths_state[aid] = list(agent.path)
        
    goals_state = {aid: task["target"] for aid, task in schedule.items()}
    
    # We will use matplotlib to render, but save to BytesIO to display in Streamlit
    h, w = grid.shape
    fig_size = max(5, min(10, w / 20))
    fig, ax = plt.subplots(1, 1, figsize=(fig_size, fig_size))
    
    display = np.zeros((h, w, 3))
    for r in range(h):
        for c in range(w):
            if grid[r, c] == 1:
                display[r, c] = [0.173, 0.243, 0.314]
            else:
                display[r, c] = [0.926, 0.941, 0.945]
                
    ax.imshow(display, interpolation='nearest')
    
    # Draw goals
    for aid, (gr, gc) in goals_state.items():
        ax.plot(gc, gr, '*', color='#9B59B6', markersize=12)
        
    # Draw agents
    for aid, (ar, ac, atype, active) in agents_state.items():
        color = '#3498DB' if active else '#95A5A6'
        marker = 'o' if active else 'X'
        ax.plot(ac, ar, marker, color=color, markersize=10)
        ax.annotate(aid[-3:], (ac, ar), fontsize=6, ha='center', va='bottom', color='white')
        
    ax.set_title(f"Step {step}")
    ax.axis('off')
    
    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches='tight')
    plt.close(fig)
    return buf

if start_btn:
    st.session_state.logs = []
    st.session_state.step = 0
    st.session_state.finished = False

    # Initialize layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Live Grid View")
        image_placeholder = st.empty()
        
    with col2:
        st.subheader("📡 Mission Control Log")
        log_placeholder = st.empty()
        
        st.subheader("📈 Live Metrics")
        metric_col1, metric_col2 = st.columns(2)
        m_step = metric_col1.metric("Current Step", 0)
        m_active = metric_col2.metric("Active Agents", 4)
        m_failures = metric_col1.metric("Failures", 0)
        m_recoveries = metric_col2.metric("Recoveries", 0)

    def log(msg, emoji="ℹ️"):
        st.session_state.logs.append(f"{emoji} {msg}")
        # Keep last 10 logs
        st.session_state.logs = st.session_state.logs[-15:]
        log_placeholder.markdown("\n".join(f"- {l}" for l in reversed(st.session_state.logs)))

    # 1. Setup Environment
    log(f"Loading {domain_choice} map...", "🗺️")
    map_file = MAP_FILES[domain_choice]
    grid, h, w = GridParser.parse_map(map_file)
    env = CrossCoordEnv(grid)
    
    # 2. Setup AI
    if use_real_llm and api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        llm = CrossCoordLLM(api_key=api_key)
        log("Connected to OpenAI API", "🟢")
    else:
        llm = CrossCoordLLM(api_key=None)
        log("Using MockLLM Backend", "🟡")
        
    # 3. Tier 1 Planning
    planner = Tier1CloudLLM(llm)
    log(f"Tier-1 Cloud decomposing mission...", "☁️")
    subtasks = planner.decompose_mission(f"Conduct {domain_choice.replace('_', ' ')} operations.")
    log(f"Generated {len(subtasks)} subtasks", "✅")
    
    # 4. Spawn Agents
    safe = np.argwhere(grid == 0)
    indices = np.random.choice(len(safe), size=4, replace=False)
    safe_positions = [tuple(safe[i]) for i in indices]
    
    agent_defs = [("A_003", "UAV_Quad"), ("A_004", "UAV_Heavy"), 
                  ("A_005", "UGV_Scout"), ("A_006", "UGV_Carrier")]
    tier3_agents = {}
    for i, (aid, atype) in enumerate(agent_defs):
        agent = Tier3Executor(aid, atype, env, safe_positions[i])
        tier3_agents[aid] = agent
        
    # 5. Tier 2 Dispatch
    log(f"Tier-2 Dispatcher allocating tasks...", "📱")
    agent_registry = {aid: agent.agent_type for aid, agent in tier3_agents.items()}
    dispatcher = Tier2DeviceLLM(llm, agent_registry)
    schedule = dispatcher.allocate_tasks(subtasks, domain_choice)
    
    # Assign goals and compute initial paths
    for aid, task in schedule.items():
        target = task["target"]
        target = (min(target[0], h-1), min(target[1], w-1))
        if grid[target] == 1:
            dists = np.abs(safe[:, 0] - target[0]) + np.abs(safe[:, 1] - target[1])
            target = tuple(safe[np.argmin(dists)])
        task["target"] = target
        tier3_agents[aid].compute_path(target)
        log(f"Assigned task {task['id']} to {aid}", "🎯")
        
    # 6. Self Healing Monitor
    healer = SelfHealingCoordinator(dispatcher, {aid: failure_rate for aid in tier3_agents})
    
    failures = 0
    recoveries = 0
    
    # --- MAIN SIMULATION LOOP ---
    max_steps = 500
    for step in range(1, max_steps + 1):
        st.session_state.step = step
        
        # Self-Healing Check
        failed_aid = healer.heartbeat_check(tier3_agents, step)
        if failed_aid:
            failures += 1
            log(f"Agent {failed_aid} failed!", "🚨")
            m_failures.metric("Failures", failures)
            
            # Redistribute
            schedule = healer.redistribute_tasks(failed_aid, schedule, tier3_agents, domain_choice)
            log(f"Tasks redistributed by Tier-2", "🔄")
            recoveries += 1
            m_recoveries.metric("Recoveries", recoveries)
            
            # Recompute paths for newly assigned agents
            for aid, task in schedule.items():
                if tier3_agents[aid].is_active and not tier3_agents[aid].path:
                    tier3_agents[aid].compute_path(task["target"])
        
        # Move Agents
        all_idle = True
        active_count = 0
        for aid, agent in tier3_agents.items():
            if not agent.is_active:
                continue
            active_count += 1
            status = agent.step()
            if status == "MOVING" or status == "BLOCKED":
                all_idle = False
            elif status == "IDLE" and aid in schedule:
                log(f"{aid} reached destination!", "🏁")
                del schedule[aid]
                
        # Update metrics
        m_step.metric("Current Step", step)
        m_active.metric("Active Agents", active_count)
        
        # Render frame
        img_buf = render_frame(grid, tier3_agents, schedule, step)
        image_placeholder.image(img_buf)
        
        # Delay
        time.sleep(sim_speed / 1000.0)
        
        if all_idle and not schedule:
            log("MISSION ACCOMPLISHED!", "🎉")
            st.success("Mission completed successfully!")
            break
            
        if active_count == 0:
            log("ALL AGENTS FAILED. MISSION ABORTED.", "☠️")
            st.error("Mission failed. All agents dropped out.")
            break
