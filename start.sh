#!/bin/bash

# SecurityLLMLab Startup Script for Linux/macOS

set -e

echo "[INFO] Starting SecurityLLMLab Setup..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    exit 1
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose is not installed."
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo "[INFO] Creating .env from .env.example..."
    if [ -f env.example ]; then
        cp env.example .env
    else
        echo "[WARNING] env.example not found. Creating empty .env."
        touch .env
    fi
else
    echo "[INFO] .env file already exists."
fi

# Build and Start Services
echo "[INFO] Building and starting services with Docker Compose..."
# Support both 'docker-compose' and 'docker compose'
if command -v docker-compose &> /dev/null; then
    docker-compose up --build -d
else
    docker compose up --build -d
fi

echo ""
echo "[SUCCESS] SecurityLLMLab is running!"
echo "[INFO] Frontend:    http://localhost:5173"
echo "[INFO] Backend API: http://localhost:8000/docs"
echo "[INFO] Kibana:      http://localhost:5601"
echo "[INFO] Qdrant:      http://localhost:6333/dashboard"
echo ""
