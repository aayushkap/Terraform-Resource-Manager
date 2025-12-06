from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from monitoring.monitoring_service import MonitoringService
import asyncio
import json

app = FastAPI()
monitor = MonitoringService()
monitor.start()

clients = set()


@app.websocket("/ws/metrics")
async def metrics_websocket(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            data = monitor.get_data()
            await websocket.send_text(data)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        clients.remove(websocket)
    except Exception:
        clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("monitoring.main:app", host="127.0.0.1", port=8000, reload=True)
