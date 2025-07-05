from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

# Datenmodell für RR-Intervalle
class RRData(BaseModel):
    timestamp: datetime
    rr: int

# In-Memory-Datenspeicher
rr_data_store: List[RRData] = []

@app.post("/rr/update", summary="Update RR data", response_description="RR-Daten erfolgreich gespeichert")
def update_rr_data(rr_intervals: List[RRData]):
    """
    Nimmt eine Liste von RR-Werten mit Timestamps entgegen und speichert sie.
    """
    try:
        rr_data_store.extend(rr_intervals)
        return {
            "status": "OK",
            "count": len(rr_intervals),
            "message": f"{len(rr_intervals)} RR-Werte gespeichert."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fehler beim Speichern der RR-Daten: {e}")
