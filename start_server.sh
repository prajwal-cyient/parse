#!/usr/bin/env bash
echo "==================================================="
echo "  Starting Parker DO-178C Platform 2.0"
echo "==================================================="

echo "[1/3] Checking Python installation..."
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 not found. Please install Python 3.10+."; exit 1; }

echo "[2/3] Installing dependencies..."
pip install -r requirements.txt

echo "[3/3] Launching server on http://localhost:8080..."
cd app/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
