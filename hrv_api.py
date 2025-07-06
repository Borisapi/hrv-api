from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
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

# Load data on start
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

# PAGINATED /all ENDPOINT
@app.get("/all", response_model=list[HRVFullData], summary="Alle gespeicherten Daten anzeigen (paginierte Version)")
def get_all_data(
    skip: int = Query(0, ge=0, description="How many records to skip (offset)"),
    limit: int = Query(1000, ge=1, le=10000, description="How many records to return in this page"),
):
    """
    Returns a page of HRV data entries (default 1000 per call).
    Example: /all?skip=0&limit=1000 (first page), /all?skip=1000&limit=1000 (second page)
    """
    return data_store[skip: skip + limit]

@app.get("/latest", response_model=Optional[HRVFullData], summary="Letzter empfangener Eintrag")
def get_latest():
    return data_store[-1] if data_store else None

@app.get("/download_hrv_json", summary="Download raw HRV JSON file")
def download_hrv_json():
    if os.path.exists(DATA_FILE):
        return FileResponse(DATA_FILE, media_type="application/json", filename=DATA_FILE)
    else:
        return {"error": "File not found."}

@app.get("/data_by_time", response_model=list[HRVFullData], summary="Get data between two timestamps")
def data_by_time(
    start: datetime = Query(..., description="Start timestamp (ISO format)"),
    end: datetime = Query(..., description="End timestamp (ISO format)")
):
    return [d for d in data_store if start <= d.timestamp <= end]

