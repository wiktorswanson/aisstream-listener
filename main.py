import asyncio
import json
from fastapi import FastAPI, WebSocket
import websockets

app = FastAPI()
clients = set()
@app.get("/")
def root():
    return {"message": "AISstream backend is running. Use /ws for WebSocket."}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except:
        clients.remove(websocket)

async def connect_to_aisstream():
    AISSTREAM_URL = "wss://stream.aisstream.io/v0/stream"
    API_KEY = "940bf3259b0a8f7c3e1e4fb317b37bba918072fa"

    async with websockets.connect(AISSTREAM_URL) as ais_ws:
        subscription_message = {
            "APIKey": API_KEY,
            "BoundingBoxes": [[[55.0, 12.0], [60.0, 18.0]]],
            "FilterMessageTypes": ["PositionReport"]
        }

        await ais_ws.send(json.dumps(subscription_message))

        while True:
            try:
                raw_data = await ais_ws.recv()
                for client in list(clients):
                    try:
                        await client.send_text(raw_data)
                    except:
                        clients.remove(client)
            except Exception as e:
                print(f"Error: {e}")
                break

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(connect_to_aisstream())
