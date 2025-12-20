from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from redis.exceptions import ConnectionError
from typing import Optional
import json
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from utils.redis_service import RedisService
from utils.logger_service import Logger
from utils.config_service import config, ScalingConfig

logger = Logger(__file__).get_logger()

app = FastAPI(title="Redis State API")

try:
    redis_service = RedisService(host="localhost", port=6379, db=0)
except ConnectionError as e:
    raise RuntimeError(f"Could not connect to Redis: {e}")

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def decode_value(value):
    """Helper to decode bytes and parse JSON"""
    if isinstance(value, bytes):
        value = value.decode()
    try:
        return json.loads(value)
    except Exception:
        return value


@app.get("/dump", response_class=JSONResponse)
def dump_all_keys():
    """Return all key-value pairs including lists and sets."""
    try:
        client = redis_service.client
        data = {}

        for key in client.scan_iter("*"):
            try:
                key_str = key.decode() if isinstance(key, bytes) else key
                key_type = client.type(key)

                if key_type == "string":
                    val = client.get(key)
                    data[key_str] = decode_value(val)

                elif key_type == "list":
                    items = client.lrange(key, 0, -1)
                    data[key_str] = [decode_value(item) for item in items]

                elif key_type == "set":
                    data[key_str] = list(client.smembers(key))

                elif key_type == "hash":
                    data[key_str] = client.hgetall(key)

                elif key_type == "zset":
                    data[key_str] = client.zrange(key, 0, -1, withscores=True)

            except Exception as e:
                print(f"Error processing key {key}: {e}")
                continue

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/global", response_class=JSONResponse)
def get_global_metrics():
    """Get current global metrics."""
    try:
        client = redis_service.client

        metrics = client.get("global:metrics")

        history = client.lrange("global:metrics:history", 0, -1)

        if not metrics:
            raise HTTPException(status_code=404, detail="Global metrics not found")

        current_metrics = decode_value(metrics)
        history = [json.loads(item) for item in history] if history else []

        return {**current_metrics, "history": history}

    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/containers", response_class=JSONResponse)
def get_all_containers_info():
    client = redis_service.client
    pattern = "container:*:info"

    containers = []
    cursor = 0

    while True:
        cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)

        for key in keys:
            key_str = key.decode() if isinstance(key, bytes) else key
            parts = key_str.split(":")  # ['container', '{id}', 'info']
            container_id = parts[1]

            info_key = f"container:{container_id}:info"
            info_type = client.type(info_key)
            if isinstance(info_type, bytes):
                info_type = info_type.decode()

            if info_type == "hash":
                info_raw = client.hgetall(info_key)
                info_decoded = {
                    k.decode(): decode_value(v) for k, v in info_raw.items()
                }
            elif info_type == "string":
                val = client.get(info_key)
                info_decoded = decode_value(val)
            else:
                info_decoded = None

            history_key = f"container:{container_id}:history"
            history_type = client.type(history_key)
            if isinstance(history_type, bytes):
                history_type = history_type.decode()

            if history_type == "list":
                history_raw = client.lrange(history_key, 0, -1)
                history_decoded = [decode_value(i) for i in history_raw]
            else:
                history_decoded = []

            containers.append(
                {
                    "id": container_id,
                    "info": info_decoded,
                    "history": history_decoded,
                }
            )

        if cursor == 0:
            break

    return containers


@app.get("/containers/{container_id}", response_class=JSONResponse)
def get_container_info(container_id: str, limit: Optional[int] = None):
    """Get info and history for a specific container."""
    try:
        client = redis_service.client

        info_key = f"container:{container_id}:info"
        info_type = client.type(info_key)
        if isinstance(info_type, bytes):
            info_type = info_type.decode()

        if info_type == "none":
            raise HTTPException(
                status_code=404, detail=f"Container {container_id} not found"
            )

        if info_type == "hash":
            raw_info = client.hgetall(info_key)
            info = {k.decode(): decode_value(v) for k, v in raw_info.items()}
        elif info_type == "string":
            val = client.get(info_key)
            info = decode_value(val)
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected key type '{info_type}' for container info",
            )

        history_key = f"container:{container_id}:history"
        history_type = client.type(history_key)
        if isinstance(history_type, bytes):
            history_type = history_type.decode()

        if history_type == "list":
            end = limit - 1 if limit else -1
            raw_history = client.lrange(history_key, 0, end)
            history = [decode_value(item) for item in raw_history]
        else:
            history = []

        if isinstance(info, dict):
            info["history"] = history
        else:
            info = {"value": info, "history": history}

        return info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system/events", response_class=JSONResponse)
def get_system_events(limit: Optional[int] = None):
    """Get system events. Use limit parameter to restrict results."""
    try:
        client = redis_service.client
        end = limit - 1 if limit else -1
        items = client.lrange("system:events", 0, end)

        return [decode_value(item) for item in items]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-config")
def update_config(new_config: ScalingConfig):
    with config._lock:
        config.config = new_config.model_dump()
        config._save_config()
    return {"status": "ok"}


@app.get("/health", response_class=JSONResponse)
def health_check():
    """Check Redis connection health."""
    try:
        client = redis_service.client
        client.ping()
        return {"status": "healthy", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unhealthy: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app", host="0.0.0.0", port=8081, log_level="info", reload=True
    )
