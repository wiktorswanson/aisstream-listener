import asyncio
import json
from fastapi import FastAPI, WebSocket
import websockets

app = FastAPI()
clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except:
        clients.remove(websocket)

async def stream_ais_data():
    url = "wss://stream.aisstream.io/v0/stream"
    API_KEY = "940bf3259b0a8f7c3e1e4fb317b37bba918072fa"
    async with websockets.connect(url) as ws:
        auth_msg = {
            "APIKey": API_KEY,
            "BoundingBoxes": [
                {"MinLat": 55.0, "MinLon": 12.0, "MaxLat": 60.0, "MaxLon": 18.0}
            ]
        }
        await ws.send(json.dumps(auth_msg))
        while True:
            msg = await ws.recv()
            for client in clients:
                try:
                    await client.send_text(msg)
                except:
                    clients.remove(client)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(stream_ais_data())
