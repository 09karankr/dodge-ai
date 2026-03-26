#!/bin/bash

# Configuration
PROJECT_ROOT="/Users/aryankumar/Desktop/Dodge-ai"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/dodge-ui"

echo "Starting O2C Graph System..."

# 1. Start Backend
echo "Starting Backend on port 8000..."
cd "$BACKEND_DIR"
nohup ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# 2. Start Frontend
echo "Starting Frontend on port 5173..."
cd "$FRONTEND_DIR"
nohup npm run dev -- --host 0.0.0.0 --port 5173 > frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo "------------------------------------------------"
echo "Services starting in background."
echo "Check backend.log and frontend.log for details."
echo "Application will be available at: http://localhost:5173"
echo "------------------------------------------------"
