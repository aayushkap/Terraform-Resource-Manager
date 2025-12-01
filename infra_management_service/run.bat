@echo off
REM Navigate to project root
cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Step 1: Run Terraform container and wait for completion
cd terraform
docker-compose run --rm terraform destroy -auto-approve
docker network prune -f
echo Starting Terraform container...
docker-compose run --rm terraform init
docker-compose run --rm terraform apply -var="server_count=1" -auto-approve
cd ..

REM Step 2: Pull and run Redis container on default port
echo Pulling and starting Redis container...
docker pull redis:latest
docker rm -f redis-server 2>nul
docker run -d --name redis-server -p 6379:6379 redis:latest

REM Step 3: Run the Python services in parallel
echo Starting services...
start cmd /k python -m management.main
start cmd /k python -m monitoring.main
start cmd /k python -m gateway.main
start cmd /k python -m api.main

echo All services started after Terraform completed.
