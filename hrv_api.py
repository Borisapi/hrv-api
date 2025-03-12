import asyncio
import datetime
import json
from fastapi import FastAPI, WebSocket
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
    """ Gibt die neuesten HRV-Daten als JSON zurück """
    if latest_hrv_data["timestamp"] is None:
        return JSONResponse(status_code=404, content={"error": "Noch keine HRV-Daten verfügbar"})
    return latest_hrv_data

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

async def update_hrv_data(heart_rate, rmssd, sdnn, lf_hf, pnn50):
    """ Aktualisiert die neuesten HRV-Daten und sendet sie an WebSocket-Clients """
    latest_hrv_data.update({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "heart_rate": heart_rate,
        "rmssd": rmssd,
        "sdnn": sdnn,
        "lf_hf": lf_hf,
        "pnn50": pnn50
    })

    # Daten an alle verbundenen WebSocket-Clients senden
    for client in websocket_clients:
        try:
            await client.send_text(json.dumps(latest_hrv_data))
        except Exception:
            websocket_clients.remove(client)

# Starte die API
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)