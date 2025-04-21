import asyncio
import websockets
import json

API_KEY = "940bf3259b0a8f7c3e1e4fb317b37bba918072fa"

async def connect_to_aisstream():
    url = "wss://stream.aisstream.io/v0/stream"

    async with websockets.connect(url) as websocket:
        auth_msg = {
            "APIKey": API_KEY,
            "BoundingBoxes": [
                {
                    "MinLat": 55.0,
                    "MinLon": 12.0,
                    "MaxLat": 60.0,
                    "MaxLon": 18.0
                }
            ]
        }

        await websocket.send(json.dumps(auth_msg))
        print("Connected and authenticated. Listening for messages...")

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(json.dumps(data, indent=2))

asyncio.run(connect_to_aisstream())
