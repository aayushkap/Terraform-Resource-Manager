from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from redis.exceptions import ConnectionError
from typing import Dict, Any
import json

from utils.redis_service import RedisService

app = FastAPI(title="Redis State API")

try:
    redis_service = RedisService(host="localhost", port=6379, db=0)
except ConnectionError as e:
    raise RuntimeError(f"Could not connect to Redis: {e}")


@app.get("/dump", response_class=JSONResponse)
def dump_all_keys():
    """Return all key-value pairs (raw)."""
    try:
        client = redis_service.client
        data = {}

        for key in client.scan_iter("*"):
            try:
                val = client.get(key)
                if val is None:
                    continue
                try:
                    val = json.loads(val)
                except Exception:
                    val = val.decode() if isinstance(val, bytes) else val
                data[key.decode() if isinstance(key, bytes) else key] = val
            except Exception:
                # skip non-string types
                continue

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
