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
                    try:
                        val = json.loads(val)
                    except Exception:
                        val = val.decode() if isinstance(val, bytes) else val
                    data[key_str] = val

                elif key_type == "list":
                    # Fetch all list items
                    items = client.lrange(key, 0, -1)
                    data[key_str] = [
                        json.loads(item) if isinstance(item, str) else item
                        for item in items
                    ]

                elif key_type == "set":
                    # Fetch all set members
                    data[key_str] = list(client.smembers(key))

                elif key_type == "hash":
                    # Fetch all hash fields
                    data[key_str] = client.hgetall(key)

                elif key_type == "zset":
                    # Fetch all sorted set members
                    data[key_str] = client.zrange(key, 0, -1, withscores=True)

            except Exception as e:
                print(f"Error processing key {key}: {e}")
                continue

        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
