import asyncio
import datetime
import json
import os
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
    """Empfängt neue HRV-Daten und aktualisiert sie für alle WebSocket-Clients."""
    latest_hrv_data.update({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "heart_rate": data.get("heart_rate"),
        "rmssd": data.get("rmssd"),
        "sdnn": data.get("sdnn"),
        "lf_hf": data.get("lf_hf"),
        "pnn50": data.get("pnn50")
    })

    # Daten an alle verbundenen WebSocket-Clients senden
    await broadcast_hrv_data()

    return {"message": "HRV-Daten aktualisiert", "data": latest_hrv_data}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket-Verbindung für Echtzeit-HRV-Daten."""
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)  # Halte die Verbindung offen
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

async def broadcast_hrv_data():
    """Sendet aktuelle HRV-Daten an alle verbundenen WebSocket-Clients."""
    if not websocket_clients:
        return

    data = json.dumps(latest_hrv_data)
    disconnected_clients = set()
    
    for client in websocket_clients:
        try:
            await client.send_text(data)
        except WebSocketDisconnect:
            disconnected_clients.add(client)
    
    # Entferne inaktive WebSocket-Clients
    for client in disconnected_clients:
        websocket_clients.remove(client)

# Starte die API mit dynamischem Port für Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render nutzt automatisch den richtigen Port
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
