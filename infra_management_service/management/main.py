from management.autoscaler import AutoScaler
import asyncio
import websockets
import json
import signal
import sys
import threading
from utils.logger_service import Logger

logger = Logger(__file__).get_logger()

class Monitor:
    def __init__(self):
        self.data = []
        self._lock = threading.Lock()

    def set_data(self, data):
        with self._lock:
            self.data = data

    def get_data(self):
        with self._lock:
            return self.data.copy()


async def receive_from_websocket(uri, monitor):
    """Continuously receive metrics from monitoring WebSocket."""
    retry_delay = 5
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Connected to {uri}")
                while True:
                    message = await websocket.recv()
                    container_info = json.loads(message)
                    monitor.set_data(container_info)  # Synchronous call

        except Exception as e:
            logger.error(f" WebSocket error: {e}, reconnecting in {retry_delay}s...")
            await asyncio.sleep(retry_delay)


async def main():
    websocket_uri = "ws://localhost:8000/ws/metrics"

    monitor = Monitor()
    autoscaler = AutoScaler(monitor, terraform_dir="./terraform")

    # Create websocket & auto_scaler tasks
    websocket_task = asyncio.create_task(receive_from_websocket(websocket_uri, monitor))
    autoscaler_task = asyncio.create_task(autoscaler.start())

    logger.info("Management service started")

    # await completion
    await asyncio.gather(websocket_task, autoscaler_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(" Shutting down...")
