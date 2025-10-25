@echo off
REM Navigate to project root
cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Step 1: Run Terraform container and wait for completion
cd terraform
echo Starting Terraform container...
docker-compose run --rm terraform apply -var="server_count=1" -auto-approve
cd ..

REM Step 2: Run the Python services in parallel (after Terraform completes)
echo Starting services...
start cmd /k python -m management.main
start cmd /k python -m monitoring.main

echo All services started after Terraform completed.
pause
