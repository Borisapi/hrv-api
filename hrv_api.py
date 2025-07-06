from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
import os

app = FastAPI(title="HRV API", version="2.0.0")

class HRVFullData(BaseModel):
    timestamp: datetime
    rr: int
    HR: float
    hrv_metrics: Optional[dict] = {}

DATA_FILE = "hrv_data.json"
data_store: list[HRVFullData] = []

# Daten beim Start laden
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        raw = json.load(f)
        data_store = [HRVFullData(**item) for item in raw]

def save_to_file():
    with open(DATA_FILE, "w") as f:
        json.dump([d.dict() for d in data_store], f, indent=2, default=str)

@app.get("/", summary="API-Status")
def root_status():
    return {"status": "HRV API läuft – bitte POST verwenden für Datenübermittlung"}

@app.post("/", summary="Empfängt vollständige HRV-Daten")
def receive_hrv_data(data: HRVFullData):
    data_store.append(data)
    save_to_file()
    return {"status": "OK", "stored": len(data_store)}

@app.get("/all", response_model=list[HRVFullData], summary="Alle gespeicherten Daten anzeigen")
def get_all_data():
    return data_store

@app.get("/latest", response_model=Optional[HRVFullData], summary="Letzter empfangener Eintrag")
def get_latest():
    return data_store[-1] if data_store else None
