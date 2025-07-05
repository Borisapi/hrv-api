import asyncio
import datetime
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

app = FastAPI()

latest_hrv_data = {
    "timestamp": None,
    "heart_rate": None,
    "rmssd": None,
    "sdnn": None,
    "lf_hf": None,
    "pnn50": None
}

latest_rr_data = {
    "timestamp": None,
    "rr_intervals": []
}

websocket_clients_hrv = set()
websocket_clients_rr = set()

@app.get("/hrv")
async def get_hrv_data():
    if latest_hrv_data["timestamp"] is None:
        return JSONResponse(status_code=404, content={"error": "Noch keine HRV-Daten verfügbar"})
    return latest_hrv_data

@app.post("/hrv/update")
async def update_hrv_data(data: dict):
    latest_hrv_data.update({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "heart_rate": data.get("heart_rate"),
        "rmssd": data.get("rmssd"),
        "sdnn": data.get("sdnn"),
        "lf_hf": data.get("lf_hf"),
        "pnn50": data.get("pnn50")
    })
    await broadcast_data(latest_hrv_data, websocket_clients_hrv)
    return {"message": "HRV-Daten aktualisiert", "data": latest_hrv_data}

@app.post("/rr/update")
async def update_rr_data(data: dict):
    latest_rr_data.update({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "rr_intervals": data.get("rr_intervals", [])
    })
    await broadcast_data(latest_rr_data, websocket_clients_rr)
    return {"message": "RR-Daten aktualisiert", "data": latest_rr_data}

@app.get("/rr")
async def get_rr_data():
    if latest_rr_data["timestamp"] is None:
        return JSONResponse(status_code=404, content={"error": "Noch keine RR-Daten verfügbar"})
    return latest_rr_data

@app.websocket("/ws/hrv")
async def websocket_hrv(websocket: WebSocket):
    await websocket.accept()
    websocket_clients_hrv.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        websocket_clients_hrv.remove(websocket)

@app.websocket("/ws/rr")
async def websocket_rr(websocket: WebSocket):
    await websocket.accept()
    websocket_clients_rr.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        websocket_clients_rr.remove(websocket)

async def broadcast_data(data, clients):
    if not clients:
        return
    message = json.dumps(data)
    disconnected_clients = set()
    for client in clients:
        try:
            await client.send_text(message)
        except WebSocketDisconnect:
            disconnected_clients.add(client)
    for client in disconnected_clients:
        clients.remove(client)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
