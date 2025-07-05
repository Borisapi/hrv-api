from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

# Einzelnes RR-Datenobjekt
class RRData(BaseModel):
    timestamp: datetime
    rr: int

# Eingabemodell für den Body
class RRDataBatch(BaseModel):
    rr_intervals: List[RRData]

# In-Memory-Speicher
rr_data_store: List[RRData] = []

@app.post("/rr/update", summary="Update RR data", response_description="RR-Daten erfolgreich gespeichert")
def update_rr_data(batch: RRDataBatch):
    """
    Empfängt und speichert eine Liste von RR-Werten mit Timestamps.
    """
    rr_data_store.extend(batch.rr_intervals)
    return {
        "status": "OK",
        "count": len(batch.rr_intervals)
    }
