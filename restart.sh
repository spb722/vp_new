#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Killing existing uvicorn process..."
pkill -f "uvicorn app:app" || echo "No process found, continuing."

echo "Pulling latest code..."
git pull

echo "Starting uvicorn in background..."
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &

echo "Started with PID $!"
