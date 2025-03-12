import asyncio
import datetime
import json
import os
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

# FastAPI-Instanz mit korrekter OpenAPI-Server-Definition
app = FastAPI(
    title="HRV API",
    description="Eine API zur Erfassung und Bereitstellung von Herzratenvariabilitätsdaten (HRV)",
    version="1.0",
    servers=[
        {"url": "https://hrv-api-5jks.onrender.com", "description": "Live API auf Render"}
    ]
)

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

@app.post("/hrv/update")
async def update_hrv_data(heart_rate: float, rmssd: float, sdnn: float, lf_hf: float, pnn50: float):
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

    return {"message": "HRV-Daten aktualisiert", "data": latest_hrv_data}

# Starte die API mit dynamischem Port für Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render nutzt automatisch den richtigen Port
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
