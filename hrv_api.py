from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(title="HRV API", version="2.0.0")

# Neues Datenmodell
class HRVFullData(BaseModel):
    timestamp: datetime
    rr: int
    HR: float
    hrv_metrics: Optional[dict] = {}

# In-Memory Speicher (z. B. für spätere Analyse oder Export)
data_store: list[HRVFullData] = []

@app.post("/", summary="Empfängt vollständige HRV-Daten")
def receive_hrv_data(data: HRVFullData):
    data_store.append(data)
    return {"status": "OK", "stored": len(data_store)}

@app.get("/all", response_model=list[HRVFullData], summary="Alle gespeicherten Daten anzeigen")
def get_all_data():
    return data_store

@app.get("/latest", response_model=Optional[HRVFullData], summary="Letzter empfangener Eintrag")
def get_latest():
    return data_store[-1] if data_store else None
