from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(title="FastAPI Load Balanced Demo")


@app.get("/")
def read_root():
    return {
        "message": "Hello fro   m FastAPI!",
        "server_id": os.getenv("SERVER_ID", "unknown"),
        "server_port": os.getenv("SERVER_PORT", "unknown"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "server_id": os.getenv("SERVER_ID", "unknown")}


@app.get("/info")
def info():
    return {
        "server_id": os.getenv("SERVER_ID", "unknown"),
        "server_port": os.getenv("SERVER_PORT", "unknown"),
        "app": "FastAPI Demo",
        "version": "1.0.0",
    }


@app.get("/stress-cpu")
def stress_cpu(n: int = 35):
    def fib(x):
        if x <= 1:
            return x
        return fib(x - 1) + fib(x - 2)

    result = fib(n)
    return {"input": n, "fib_result": result, "message": "CPU intensive task completed"}
