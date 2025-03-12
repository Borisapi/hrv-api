from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import asyncio
import datetime
import json
import os

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
        return JSONResponse(status_code=404, content={"error": "Noch keine HRV-Daten verfügbar"})
    return latest_hrv_data

@app.post("/hrv")
async def receive_hrv_data(data: HRVData):
    """ Empfängt HRV-Daten und speichert sie """
    latest_hrv_data.update({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "heart_rate": data.heart_rate,
        "rmssd": data.rmssd,
        "sdnn": data.sdnn,
        "lf_hf": data.lf_hf,
        "pnn50": data.pnn50
    })

    # Daten an alle verbundenen WebSocket-Clients senden
    for client in websocket_clients:
        try:
            await client.send_text(json.dumps(latest_hrv_data))
        except Exception:
            websocket_clients.remove(client)

    return {"message": "HRV-Daten erfolgreich empfangen"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ WebSocket-Verbindung für Echtzeit-HRV-Daten """
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except Exception:
        pass
    finally:
        websocket_clients.remove(websocket)

# Starte die API mit dynamischem Port für Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render nutzt automatisch den richtigen Port
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
