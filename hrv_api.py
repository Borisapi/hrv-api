import asyncio
import datetime
import json
import os
from typing import List, Optional

import numpy as np
from scipy.signal import welch

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

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

# Liste der aktiven WebSocket-Verbindungen
websocket_clients = set()

@app.get("/hrv")
async def get_hrv_data():
    """Gibt die neuesten HRV-Daten als JSON zurück."""
    if latest_hrv_data["timestamp"] is None:
        return JSONResponse(status_code=404, content={"error": "Noch keine HRV-Daten verfügbar"})
    return latest_hrv_data

@app.post("/hrv/update")
async def update_hrv_data(data: dict):
    """Empfängt neue HRV-Daten (berechnet oder roh) und aktualisiert sie für alle WebSocket-Clients."""

    # Wenn RR-Werte gesendet wurden, berechne HRV-Metriken
    rr_values: Optional[List[int]] = data.get("rr_values")
    if rr_values:
        rr_array = np.array([rr for rr in rr_values if 300 <= rr <= 2000])
        if len(rr_array) >= 60:
            diff_rr = np.diff(rr_array)
            rmssd = np.sqrt(np.mean(diff_rr ** 2))
            sdnn = np.std(rr_array, ddof=1)
            nn50 = np.sum(np.abs(diff_rr) > 50)
            pnn50 = nn50 / len(diff_rr)
            
            # Frequenzanalyse (interpoliert)
            time = np.cumsum(rr_array) / 1000.0
            interpolated_rr = np.interp(np.linspace(time[0], time[-1], len(time)), time, rr_array)
            freqs, psd = welch(interpolated_rr, fs=4.0, nperseg=min(256, len(interpolated_rr)))
            lf_band = (0.04, 0.15)
            hf_band = (0.15, 0.4)
            lf_mask = (freqs >= lf_band[0]) & (freqs < lf_band[1])
            hf_mask = (freqs >= hf_band[0]) & (freqs < hf_band[1])
            lf_power = np.trapz(psd[lf_mask], freqs[lf_mask])
            hf_power = np.trapz(psd[hf_mask], freqs[hf_mask])
            lf_hf = lf_power / hf_power if hf_power > 0 else None

            hr = 60000 / np.mean(rr_array)

            latest_hrv_data.update({
                "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "heart_rate": hr,
                "rmssd": rmssd,
                "sdnn": sdnn,
                "lf_hf": lf_hf,
                "pnn50": pnn50
            })
    else:
        # Übernehme bereits berechnete Werte, falls vorhanden
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket-Verbindung für Echtzeit-HRV-Daten."""
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

async def broadcast_hrv_data():
    """Sendet aktuelle HRV-Daten an alle verbundenen WebSocket-Clients."""
    if not websocket_clients:
        return
    data = json.dumps(latest_hrv_data, default=str)
    disconnected = set()
    for ws in websocket_clients:
        try:
            await ws.send_text(data)
        except WebSocketDisconnect:
            disconnected.add(ws)
    websocket_clients.difference_update(disconnected)

# Starte die API mit dynamischem Port für Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
