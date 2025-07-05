from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

app = FastAPI(title="HRV API", version="1.2.0")

# ---------- Datenmodelle ----------
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

class RRDataBatch(BaseModel):
    rr_intervals: List[RRData]

# ---------- Speicher ----------
rr_data_store: List[RRData] = []
latest_hrv: HRVData | None = None

# ---------- Endpunkte ----------
@app.post("/rr/update", summary="Update RR data")
def update_rr_data(batch: RRDataBatch):
    # Typ-Sicherheit: Immer echte RRData-Objekte
    for item in batch.rr_intervals:
        if not isinstance(item, RRData):
            item = RRData(**item.dict())
        rr_data_store.append(item)
    return {"status": "OK", "count": len(batch.rr_intervals)}

@app.get("/rr/all", response_model=List[RRData])
def get_all_rr_data():
    return rr_data_store

@app.get("/rr/recent", response_model=List[RRData])
def get_recent_rr_data(minutes: int = Query(2, ge=1, le=60)):
   from datetime import timezone
cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    try:
        return [entry for entry in rr_data_store if entry.timestamp >= cutoff]
    except Exception as e:
        print(f"Fehler in /rr/recent: {e}, Daten: {rr_data_store[-3:]}")
        raise

@app.get("/rr", response_model=List[int])
def get_rr_intervals():
    # Rohdaten, ohne Zeitstempel (z.B. für Legacy-Nutzer)
    return [entry.rr for entry in rr_data_store[-100:]]

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
