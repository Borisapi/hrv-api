from fastapi import FastAPI, WebSocket, HTTPException
from pydantic import BaseModel
import datetime
import json
import asyncio

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

# WebSocket-Clients
websocket_clients = set()

class HRVData(BaseModel):
    heart_rate: float
    rmssd: float
    sdnn: float
    lf_hf: float
    pnn50: float

@app.get("/hrv")
async def get_hrv_data():
    """ Gibt die neuesten HRV-Daten als JSON zurück """
    if latest_hrv_data["timestamp"] is None:
        raise HTTPException(status_code=404, detail="Noch keine HRV-Daten verfügbar")
    return latest_hrv_data

@app.post("/hrv/update")
async def update_hrv_data(data: HRVData):
    """ Aktualisiert die neuesten HRV-Daten """
    latest_hrv_data.update({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "heart_rate": data.heart_rate,
        "rmssd": data.rmssd,
        "sdnn": data.sdnn,
        "lf_hf": data.lf_hf,
        "pnn50": data.pnn50
    })
    return {"message": "HRV-Daten aktualisiert", "data": latest_hrv_data}
