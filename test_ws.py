import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket.")
            await websocket.send("START_SIMULATION")
            print("Sent START_SIMULATION.")
            
            # Listen for a few events to verify serialization works
            for i in range(10):
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received Event: {data['topic']}")
                
            print("Successfully received 10 events without crashing! Test passed.")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
