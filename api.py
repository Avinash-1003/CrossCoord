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
            await websocket.send_text(json.dumps(event))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        self.event_history.append(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

manager = ConnectionManager()

# We subscribe to the event bus and forward everything to the WebSocket
def handle_event(topic, payload):
    # Convert numpy arrays to lists for JSON serialization
    safe_payload = {}
    for k, v in payload.items():
        if hasattr(v, "tolist"):
            safe_payload[k] = v.tolist()
        # Handle PyTorch weights in FedAvg
        elif isinstance(v, dict) and "weights" in payload:
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
    bus.subscribe("TASK_COMPLETED", lambda p: handle_event("TASK_COMPLETED", p))
    bus.subscribe("MODEL_WEIGHTS_UPLOAD", lambda p: handle_event("FED_AVG_SYNC", {"agent_id": p.get("agent_id")}))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open, wait for client messages if any
            data = await websocket.receive_text()
            if data == "START_SIMULATION":
                # Clear history
                manager.event_history.clear()
                # Run the simulation in a background task
                asyncio.create_task(run_advanced_simulation())
    except WebSocketDisconnect:
        manager.disconnect(websocket)
