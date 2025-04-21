import asyncio
import json
import datetime
import socket
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
                print(f"[AIS ERROR] {e}")
                break

def convert_latlon(raw, direction):
    try:
        if len(raw) < 4:
            return None
        deg_len = 2 if direction in ['N', 'S'] else 3
        deg = int(raw[:deg_len])
        minutes = float(raw[deg_len:])
        val = deg + minutes / 60
        if direction in ['S', 'W']:
            val = -val
        return val
    except:
        return None

async def listen_for_gps():
    HOST = "0.0.0.0"
    PORT = 5005
    print(f"[GPS] Listening for NMEA on {HOST}:{PORT}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))
        sock.setblocking(False)
        loop = asyncio.get_event_loop()
        while True:
            try:
                data, _ = await loop.run_in_executor(None, sock.recv, 1024)
                line = data.decode("utf-8", errors="ignore").strip()
                if line.startswith("$GPRMC") or line.startswith("$GPGGA"):
                    parts = line.split(",")
                    if len(parts) > 5:
                        lat_raw = parts[3]
                        lat_dir = parts[4]
                        lon_raw = parts[5]
                        lon_dir = parts[6]
                        lat = convert_latlon(lat_raw, lat_dir)
                        lon = convert_latlon(lon_raw, lon_dir)
                        if lat is not None and lon is not None:
                            msg = {
                                "MessageType": "GPS",
                                "Lat": lat,
                                "Lon": lon,
                                "Timestamp": datetime.datetime.utcnow().isoformat()
                            }
                            for client in list(clients):
                                try:
                                    await client.send_text(json.dumps(msg))
                                except:
                                    clients.remove(client)
                            print(f"[GPS] {lat:.6f}, {lon:.6f}")
            except Exception as e:
                await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(connect_to_aisstream())
    asyncio.create_task(listen_for_gps())
