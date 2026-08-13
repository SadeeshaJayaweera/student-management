#!/bin/bash
# NSBM EduSphere — Startup Script

echo "=================================================="
echo "🎓 Starting NSBM EduSphere Application"
echo "=================================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

# Mode check: if argument is 'dev', start both backend and frontend dev server
if [ "$1" == "dev" ]; then
    echo "Starting in FULL DEV MODE (FastAPI + Vite Dev Server)..."
    ./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    cd frontend && npm run dev &
    FRONTEND_PID=$!
    echo "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
    trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
    wait
else
    echo "Starting unified server on http://localhost:8000..."
    ./venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
fi
