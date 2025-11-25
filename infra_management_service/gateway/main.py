"""
Simple API Gateway to discover and proxy requests to backend servers.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse
import httpx
import docker
import json
from collections import defaultdict
import time

app = FastAPI()
client = docker.DockerClient(base_url="npipe:////./pipe/docker_engine")
current_backend = 0
request_counters = {}
request_history = defaultdict(list)
WINDOW_SECONDS = 60


def get_backends():
    containers = client.containers.list(filters={"status": "running"})
    backends = []

    for container in containers:
        if container.name.startswith("fastapi-server"):
            ports = container.attrs["NetworkSettings"]["Ports"]
            for port_key, port_mappings in ports.items():
                if port_mappings and "8000/tcp" in port_key:
                    host_port = port_mappings[0]["HostPort"]
                    backends.append(
                        {"name": container.name, "url": f"http://localhost:{host_port}"}
                    )
                    break

    return backends


@app.get("/health")
async def health():
    """Gateway health check with backend info."""
    backends = get_backends()
    return {
        "status": "healthy",
        "backends": [b["name"] for b in backends],
        "backend_count": len(backends),
    }


@app.get("/metrics")
async def metrics(server_name: str = None):
    """Return requests per backend in last 60 seconds"""
    now = time.time()
    metrics_data = {}
    for backend, timestamps in request_history.items():
        # Count requests in the last WINDOW_SECONDS
        recent_count = len([ts for ts in timestamps if ts > now - WINDOW_SECONDS])
        metrics_data[backend] = recent_count
    if server_name:
        return {"rpm": metrics_data.get(server_name, None)}
    return metrics_data


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    global current_backend

    backends = get_backends()
    if not backends:
        return JSONResponse(content={"error": "No backends available"}, status_code=503)

    # Round-robin
    backend = backends[current_backend % len(backends)]
    current_backend = (current_backend + 1) % len(backends)

    url = f"{backend['url']}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

    print(f"Proxying {request.method} {url} -> {backend['name']}")

    now = time.time()
    request_history[backend["name"]].append(now)
    # Clean old requests beyond the window
    request_history[backend["name"]] = [
        ts for ts in request_history[backend["name"]] if ts > now - WINDOW_SECONDS
    ]

    # Forward request iwht 10 sec to
    timeout = httpx.Timeout(
        connect=10.0,
        read=120.0,
        write=10.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            body = await request.body()

            headers = dict(request.headers)
            headers.pop("host", None)

            response = await http_client.request(
                method=request.method,
                url=url,
                content=body,
                headers=headers,
                follow_redirects=True,
            )

            content_type = response.headers.get("content-type", "")

            response_headers = dict(response.headers)
            response_headers["X-Served-By"] = backend["name"]

            response_headers.pop("content-length", None)

            # inject server info
            if "application/json" in content_type:
                try:
                    response_data = response.json()

                    if isinstance(response_data, dict):
                        response_data["_server"] = backend["name"]
                    elif isinstance(response_data, list):
                        response_data = {
                            "data": response_data,
                            "_server": backend["name"],
                        }
                    else:
                        response_data = {
                            "data": response_data,
                            "_server": backend["name"],
                        }

                    return JSONResponse(
                        content=response_data,
                        status_code=response.status_code,
                        headers=response_headers,
                    )
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"JSON decode error: {e}")
                    return Response(
                        content=response.content,
                        status_code=response.status_code,
                        headers=response_headers,
                        media_type=content_type,
                    )

            # Non-JSON responses
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=content_type,
            )

    except httpx.TimeoutException as e:
        print(f"Timeout error: {e}")
        return JSONResponse(
            content={
                "error": "Request timed out - operation took too long",
                "backend": backend["name"],
                "details": str(e),
            },
            status_code=504,
        )

    except httpx.RemoteProtocolError as e:
        print(f"Protocol error: {e}")
        return JSONResponse(
            content={
                "error": "Backend returned incomplete response",
                "backend": backend["name"],
                "details": str(e),
            },
            status_code=502,
        )

    except httpx.RequestError as e:
        print(f"Request error: {e}")
        return JSONResponse(
            content={
                "error": f"Backend request failed: {str(e)}",
                "backend": backend["name"],
            },
            status_code=502,
        )

    except Exception as e:
        print(f"Unexpected error: {e}")
        return JSONResponse(
            content={
                "error": f"Unexpected error: {str(e)}",
                "backend": backend["name"],
            },
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
