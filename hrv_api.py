from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, timezone

app = FastAPI(title="HRV API", version="1.3.0")

# Datenmodelle
class RRData(BaseModel):
    timestamp: datetime
    rr: int

class RRDataBatch(BaseModel):
    rr_intervals: List[RRData]

class HRVData(BaseModel):
    timestamp: datetime
    heart_rate: float
    rmssd: Optional[float] = None
    sdnn: Optional[float] = None
    lf_hf: Optional[float] = None
    pnn50: Optional[float] = None

# In-Memory Speicher
rr_data_store: List[RRData] = []
latest_hrv: Optional[HRVData] = None

# RR Update – akzeptiert Timestamps und speichert sauber als Objekte
@app.post("/rr/update", summary="Update RR data")
def update_rr_data(batch: RRDataBatch):
    for item in batch.rr_intervals:
        # Sicherheit: Auch wenn als dict angekommen, korrekt parsen
        if not isinstance(item, RRData):
            item = RRData(**item.dict())
        rr_data_store.append(item)
    return {"status": "OK", "count": len(batch.rr_intervals)}

# RR All – Liste aller RR-Daten mit Timestamps
@app.get("/rr/all", response_model=List[RRData])
def get_all_rr_data():
    return rr_data_store

# RR Recent – Liste der letzten Minuten, Zeitvergleich UTC-sicher!
@app.get("/rr/recent", response_model=List[RRData])
def get_recent_rr_data(minutes: int = Query(2, ge=1, le=60)):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return [entry for entry in rr_data_store if entry.timestamp >= cutoff]

# RR – Nur Werte, keine Timestamps (Legacy-Client)
@app.get("/rr", response_model=List[int])
def get_rr_intervals():
    return [entry.rr for entry in rr_data_store[-100:]]

# HRV Update und Get
@app.get("/hrv", response_model=HRVData)
def get_hrv_data():
    if latest_hrv is None:
        return {"detail": "No HRV data available"}, 404
    return latest_hrv

@app.post("/hrv/update")
def update_hrv_data(hrv: HRVData):
    global latest_hrv
    latest_hrv = hrv
    return {"status": "HRV data updated"}

# Dummy WS
@app.get("/ws")
def ws_hrv_live():
    return {"detail": "WebSocket placeholder – implement if needed"}
