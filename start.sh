#!/bin/bash
# Customer Support Intelligence - Start Script (lightweight, SQLite by default)

cd "$(dirname "$0")"
echo "=== Starting Customer Support Intelligence ==="

# If PostgreSQL DATABASE_URL is explicitly set, use it. Otherwise SQLite (no DB server needed).
if grep -q "^DATABASE_URL=" .env 2>/dev/null; then
    source .env 2>/dev/null || true
fi

# Backend
echo "Starting backend (port 8000)..."
cd backend
source venv/bin/activate 2>/dev/null || true
python3 -c "
from app.core.database import engine, Base
from app.models.user import User
from app.models.dataset import Dataset
from app.models.ticket import Ticket
from app.models.analysis import Analysis
Base.metadata.create_all(bind=engine)
" 2>/dev/null
python3 seed.py >/dev/null 2>&1
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/csi_backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Frontend
echo "Starting frontend (port 5173)..."
cd frontend
nohup npm run dev > /tmp/csi_frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "$BACKEND_PID $FRONTEND_PID" > .pids

echo ""
echo "=== Services Running ==="
echo "Frontend:  http://localhost:5173"
echo "Backend:   http://localhost:8000"
echo "API Docs:  http://localhost:8000/docs"
echo ""
echo "Open http://localhost:5173"
echo "Demo: demo@example.com / DemoPassword123!"
echo ""
echo "Logs: /tmp/csi_backend.log , /tmp/csi_frontend.log"
echo "Stop with: ./stop.sh"
