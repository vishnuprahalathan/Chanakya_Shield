import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8001/ws/evaluation"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        try:
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received Packet ID: {data['packet_id']}")
                print(f"Classical Accuracy: {data['classical']['accuracy']}%")
                print(f"Quantum Accuracy: {data['quantum']['accuracy']}%")
                break # Only need one to verify
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
