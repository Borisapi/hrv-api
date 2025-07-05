import asyncio
import datetime
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# Speicher für die letzten HRV-Daten
latest_hrv_data = {
    "timestamp": None,
    "heart_rate": None,
    "rmssd": None,
    "sdnn": None,
    "lf_hf": None,
    "pnn50": None
}

# Speicher für RR-Intervalle
rr_storage = []
rr_detailed_storage = []

# WebSocket-Verbindungen
websocket_clients = set()

class RRDataPoint(BaseModel):
    timestamp: str
    rr: int

class RRUploadPayload(BaseModel):
    data: List[RRDataPoint]

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
    await broadcast_hrv_data()
    return {"message": "HRV-Daten aktualisiert", "data": latest_hrv_data}

@app.post("/rr/update")
async def update_rr_data(data: dict):
    rr_values = data.get("rr_intervals", [])
    if not isinstance(rr_values, list) or not all(isinstance(rr, int) for rr in rr_values):
        return JSONResponse(status_code=400, content={"error": "Ungültiges Format für RR-Daten"})
    rr_storage.extend(rr_values)
    return {"message": "RR-Daten erfolgreich gespeichert", "anzahl": len(rr_storage)}

@app.post("/rr/upload")
async def upload_detailed_rr_data(payload: RRUploadPayload):
    rr_detailed_storage.extend(payload.data)
    return {"message": "Detaillierte RR-Daten gespeichert", "anzahl": len(payload.data)}

@app.get("/rr")
async def get_rr_data():
    return {"rr_intervals": rr_storage}

@app.get("/rr/all")
async def get_all_detailed_rr_data():
    return rr_detailed_storage

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

async def broadcast_hrv_data():
    if not websocket_clients:
        return
    data = json.dumps(latest_hrv_data)
    disconnected_clients = set()
    for client in websocket_clients:
        try:
            await client.send_text(data)
        except WebSocketDisconnect:
            disconnected_clients.add(client)
    for client in disconnected_clients:
        websocket_clients.remove(client)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
