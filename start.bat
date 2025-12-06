@echo off
setlocal

echo [INFO] Starting SecurityLLMLab Setup for Windows...

:: Check for Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH. Please install Docker Desktop first.
    pause
    exit /b 1
)

:: Check for .env file
if not exist .env (
    echo [INFO] Creating .env from .env.example...
    copy env.example .env
    echo [INFO] .env created. Please edit it if you need specific configurations.
) else (
    echo [INFO] .env file already exists.
)

:: Build and Start Services
echo [INFO] Building and starting services with Docker Compose...
docker-compose up --build -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services. Please check Docker output.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] SecurityLLMLab is running!
echo [INFO] Frontend:    http://localhost:5173
echo [INFO] Backend API: http://localhost:8000/docs
echo [INFO] Kibana:      http://localhost:5601
echo [INFO] Qdrant:      http://localhost:6333/dashboard
echo.
pause
