from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

app = FastAPI(title="HRV API", version="1.1.0")

# Datenspeicher für RR- und HRV-Daten
class RRData(BaseModel):
    timestamp: datetime
    rr: int

class HRVData(BaseModel):
    timestamp: datetime
    heart_rate: float
    rmssd: float = None
    sdnn: float = None
    lf_hf: float = None
    pnn50: float = None

rr_data_store: List[RRData] = []
latest_hrv: HRVData | None = None

@app.get("/rr", response_model=List[int])
def get_rr_intervals():
    return [entry.rr for entry in rr_data_store[-100:]]

@app.get("/rr/all", response_model=List[RRData])
def get_all_rr_data():
    return rr_data_store

@app.get("/rr/recent", response_model=List[RRData])
def get_recent_rr_data(minutes: int = Query(5, ge=1, le=60)):
    cutoff = datetime.utcnow() - timedelta(minutes=minutes)
    return [entry for entry in rr_data_store if entry.timestamp >= cutoff]

@app.post("/rr/update")
def update_rr_data(rr_intervals: List[RRData]):
    rr_data_store.extend(rr_intervals)
    return {"status": "OK", "count": len(rr_intervals)}

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

@app.get("/ws")
def ws_hrv_live():
    return {"detail": "WebSocket placeholder – implement if needed"}
