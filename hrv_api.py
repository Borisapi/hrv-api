import asyncio
import datetime
import json
import os
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

app = FastAPI()

# Speicher für die neuesten HRV-Daten
latest_hrv_data = {
    "timestamp": None,
    "heart_rate": None,
    "rmssd": None,
    "sdnn": None,
    "lf_hf": None,
    "pnn50": None
}

# WebSocket-Verbindungen speichern
websocket_clients = set()


@app.get("/hrv")
async def get_hrv_data():
    """Gibt die neuesten HRV-Daten zurück"""
    if latest_hrv_data["timestamp"] is None:
        return JSONResponse(status_code=404, content={"error": "Noch keine HRV-Daten verfügbar"})
    return latest_hrv_data


@app.post("/hrv/update")
async def update_hrv_data(data: dict):
    """Empfängt und speichert neue HRV-Daten"""
    try:
        latest_hrv_data.update({
            "timestamp": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "heart_rate": data["heart_rate"],
            "rmssd": data["rmssd"],
            "sdnn": data["sdnn"],
            "lf_hf": data["lf_hf"],
            "pnn50": data["pnn50"]
        })

        # Daten an WebSocket-Clients senden
        for client in websocket_clients:
            try:
                await client.send_text(json.dumps(latest_hrv_data))
            except:
                websocket_clients.remove(client)

        return {"message": "HRV-Daten erfolgreich aktualisiert"}
    
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Fehlendes Feld: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """ WebSocket für Echtzeit-HRV-Daten """
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except:
        pass
    finally:
        websocket_clients.remove(websocket)


def custom_openapi():
    """ Definiert OpenAPI mit der richtigen Server-URL für OpenAI GPT Actions """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="HRV API",
        version="1.0.0",
        description="Eine API zur Erfassung und Bereitstellung von HRV-Daten",
        routes=app.routes,
    )

    # Server-URL explizit setzen
    openapi_schema["servers"] = [{"url": "https://hrv-api-5jks.onrender.com"}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Setzt die OpenAPI-Dokumentation mit korrekter Server-URL
app.openapi = custom_openapi

# Starte die API mit dynamischem Port für Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render setzt automatisch den richtigen Port
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
