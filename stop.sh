#!/bin/bash
# Customer Support Intelligence - Stop Script

cd "$(dirname "$0")"

if [ -f .pids ]; then
    PIDS=$(cat .pids)
    for PID in $PIDS; do
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            echo "Stopped process $PID"
        fi
    done
    rm -f .pids
    echo "All services stopped."
else
    echo "No .pids file found. Killing by name..."
    pkill -f "uvicorn app.main:app" 2>/dev/null && echo "Stopped backend" || echo "No backend running"
    pkill -f "npm run dev" 2>/dev/null && echo "Stopped frontend" || echo "No frontend running"
    pkill -f "vite" 2>/dev/null && echo "Stopped vite" || echo "No vite running"
fi

