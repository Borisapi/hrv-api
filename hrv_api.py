import asyncio
import datetime
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

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

# Datenmodell für POST-Anfragen
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
        raise HTTPException(status_code=404, detail="Noch keine HRV-Daten verfügbar")
    return latest_hrv_data

@app.post("/hrv")
async def post_hrv_data(data: HRVData):
    """ Empfängt und speichert neue HRV-Daten """
    latest_hrv_data.update({
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "heart_rate": data.heart_rate,
        "rmssd": data.rmssd,
        "sdnn": data.sdnn,
        "lf_hf": data.lf_hf,
        "pnn50": data.pnn50
    })

    # Sende die Daten an alle WebSocket-Clients
    await broadcast_hrv_data()

    return {"message": "HRV-Daten aktualisiert", "data": latest_hrv_data}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ WebSocket-Verbindung für Echtzeit-HRV-Daten """
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

async def broadcast_hrv_data():
    """ Sendet die aktuellen HRV-Daten an alle WebSocket-Clients """
    for client in list(websocket_clients):  # Kopie der Liste, um Disconnects zu vermeiden
        try:
            await client.send_text(json.dumps(latest_hrv_data))
        except Exception:
            websocket_clients.remove(client)

# Setze die Server-URL explizit für OpenAPI
@app.on_event("startup")
async def startup_event():
    app.openapi_schema = None  # Setze Schema zurück, um es zu aktualisieren

def custom_openapi():
    """ Anpassung der OpenAPI-Dokumentation mit der korrekten Server-URL """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = app.openapi()
    openapi_schema["servers"] = [{"url": "https://hrv-api-5jks.onrender.com"}]  # Richtige URL setzen
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi  # Überschreiben der OpenAPI-Dokumentation

# Starte die API mit dynamischem Port für Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render erkennt den Port automatisch
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
