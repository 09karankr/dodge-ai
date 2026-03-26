#!/bin/bash

echo "Stopping O2C Graph System..."

# Kill processes on known ports
echo "Killing processes on ports 8000 (Backend) and 5173 (Frontend)..."

# Port 8000 (Backend)
PID_BACKEND=$(lsof -ti:8000)
if [ -n "$PID_BACKEND" ]; then
    kill -9 $PID_BACKEND
    echo "Stopped Backend (PID: $PID_BACKEND)"
else
    echo "No process found on port 8000"
fi

# Port 5173 (Frontend)
PID_FRONTEND=$(lsof -ti:5173)
if [ -n "$PID_FRONTEND" ]; then
    kill -9 $PID_FRONTEND
    echo "Stopped Frontend (PID: $PID_FRONTEND)"
else
    echo "No process found on port 5173"
fi

echo "All services stopped."
