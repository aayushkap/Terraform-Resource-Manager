Infrastructure Management Backend Service. Monitors & Scales on Server Containers based on User Defined Metrics. Possible Metrics:

- CPU Utilization / Server
- Memory Utilization / Server
- Requests Per Minute / Server

python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8081
