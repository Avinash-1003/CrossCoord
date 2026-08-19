#!/bin/bash
echo "Starting FastAPI Backend..."
python3 -m uvicorn api:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting Vite 3D Frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "==========================================="
echo "3D DIGITAL TWIN DEPLOYED!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to stop both servers."
echo "==========================================="

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
