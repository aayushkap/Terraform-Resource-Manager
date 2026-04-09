# Terraform Resource Manager

Autoscaling for Dockerized FastAPI services with Terraform. It provisions backend containers with Terraform, routes traffic through a small gateway, monitors live Docker stats, stores state in Redis, and scales the fleet up or down based on runtime metrics.

## What It Does

- Creates and manages `fastapi-server-*` backend containers with Terraform.
- Sends traffic through a FastAPI gateway that does round-robin routing and tracks per-container request rate.
- Monitors each managed container for CPU, memory, status, logs, and request volume.
- Stores per-container snapshots, short history, system events, and aggregate metrics in Redis.
- Runs an autoscaling loop that applies min/max bounds, thresholds, cooldowns, and sustained-period checks before changing container count.
- Exposes Redis-backed state to the React UI through a small API.

## How It Works

1. Terraform builds the demo FastAPI image and brings up `fastapi-server-*` containers on a Docker network.
2. The gateway discovers running backend containers directly from Docker and proxies incoming requests to them round-robin.
3. The monitoring service watches Docker events, starts one monitoring thread per managed container, calculates CPU and memory usage from Docker stats, fetches request-rate data from the gateway, and writes the latest state to Redis.
4. The management service consumes the monitoring WebSocket stream, analyzes recent metrics using the scaling config, and queues scale-up or scale-down actions.
5. The scaler service serializes those actions and reruns Terraform with a new `server_count`.
6. The API exposes `/containers`, `/metrics/global`, and system event data so the UI can render infrastructure and observability views.

## Main Components

- [`infrastructure_manager/app`](./infrastructure_manager/app): sample FastAPI workload that gets replicated.
- [`infrastructure_manager/gateway`](./infrastructure_manager/gateway): gateway and request-rate tracker.
- [`infrastructure_manager/monitoring`](./infrastructure_manager/monitoring): Docker stats collector, Redis writer, WebSocket publisher.
- [`infrastructure_manager/management`](./infrastructure_manager/management): autoscaling decision engine and Terraform executor.
- [`infrastructure_manager/api`](./infrastructure_manager/api): Redis-backed API for the dashboard.
- [`infrastructure_manager/terraform`](./infrastructure_manager/terraform): Docker provider, image, network, and container definitions.
- [`ui`](./ui): React/Vite dashboard for topology and observability.

![`Architecture.png`](./Architecture.png)

## Running It

- Backend stack: `cd infrastructure_manager` then run `run.bat`
- UI: `cd ui && npm install && npm run dev`
- Main ports: gateway `8080`, state API `8081`, monitoring WebSocket `8000`, Redis `6379`, backend containers `9001+`

## Important Notes

- The backend is currently Windows-first: several services talk to Docker through `npipe:////./pipe/docker_engine`, and `run.bat` is the checked-in bootstrap path.
- Scaling behavior can be configured in [`infrastructure_manager/scaling_config.json`](./infrastructure_manager/scaling_config.json).
