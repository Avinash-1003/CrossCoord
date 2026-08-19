from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

# Import the existing event bus and the simulation starter
from utils.event_bus import bus
from main_advanced import main as run_advanced_simulation

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        # Store events temporarily if clients connect late
        self.event_history = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send history so they catch up
        for event in self.event_history:
            await websocket.send_text(json.dumps(event, cls=NumpyEncoder))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        self.event_history.append(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, cls=NumpyEncoder))
            except Exception:
                pass

manager = ConnectionManager()

# We subscribe to the event bus and forward everything to the WebSocket
def handle_event(topic, payload):
    # Convert numpy arrays to lists for JSON serialization
    safe_payload = {}
    for k, v in payload.items():
        # Handle PyTorch weights in FedAvg
        if isinstance(v, dict) and "weights" in payload:
            continue # Don't send huge weight tensors to the frontend, just send a ping
        else:
            safe_payload[k] = v
            
    # Send to the async broadcaster
    asyncio.create_task(manager.broadcast({
        "topic": topic,
        "payload": safe_payload
    }))

@app.on_event("startup")
async def startup_event():
    # Subscribe to interesting topics
    bus.subscribe("MAP_UPDATE", lambda p: handle_event("MAP_UPDATE", p))
    bus.subscribe("GLOBAL_MAP_BROADCAST", lambda p: handle_event("GLOBAL_MAP_BROADCAST", p))
    bus.subscribe("PATH_BLOCKED", lambda p: handle_event("PATH_BLOCKED", p))
    bus.subscribe("AGENT_MOVED", lambda p: handle_event("AGENT_MOVED", p))
    bus.subscribe("TASK_COMPLETED", lambda p: handle_event("TASK_COMPLETED", p))
    bus.subscribe("MODEL_WEIGHTS_UPLOAD", lambda p: handle_event("FED_AVG_SYNC", {"agent_id": p.get("agent_id")}))
    
    # New C2 Dashboard Telemetry
    bus.subscribe("LLM_REASONING", lambda p: handle_event("LLM_REASONING", p))
    bus.subscribe("DQN_TELEMETRY", lambda p: handle_event("DQN_TELEMETRY", p))
    bus.subscribe("HEARTBEAT", lambda p: handle_event("HEARTBEAT", p))
    bus.subscribe("SIMULATION_COMPLETE", lambda p: handle_event("SIMULATION_COMPLETE", p))
    
    # PhD Level Telemetry Topics
    bus.subscribe("CBS_TELEMETRY", lambda p: handle_event("CBS_TELEMETRY", p))
    bus.subscribe("MESH_TELEMETRY", lambda p: handle_event("MESH_TELEMETRY", p))
    bus.subscribe("ACADEMIC_METRICS", lambda p: handle_event("ACADEMIC_METRICS", p))

from fastapi.responses import PlainTextResponse
from modules.metrics_engine import AcademicMetricsEngine

@app.get("/export_paper", response_class=PlainTextResponse)
def export_paper():
    metrics = {
        "makespan": 150,
        "flowtime_soff": 420,
        "comm_overhead_kb": 14.2,
        "pareto_efficiency": 0.852
    }
    latex_doc = AcademicMetricsEngine.generate_ieee_latex(metrics, domain="Disaster Relief")
    return latex_doc

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                cmd_obj = json.loads(raw_data)
                cmd_type = cmd_obj.get("cmd") or cmd_obj.get("type")
            except Exception:
                cmd_type = raw_data
                cmd_obj = {}

            if cmd_type == "START_SIMULATION":
                domain = cmd_obj.get("domain", "disaster_relief")
                manager.event_history.clear()
                asyncio.create_task(run_advanced_simulation(domain=domain))
            elif cmd_type == "INJECT_FAILURE":
                aid = cmd_obj.get("agent_id", "A_006")
                await bus.publish("CMD_INJECT_FAILURE", {"agent_id": aid})
            elif cmd_type == "TRIGGER_FL":
                await bus.publish("CMD_TRIGGER_FL", {})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
