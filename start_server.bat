@echo off
title Parker DO-178C Verification Platform 2.0
echo ===================================================
echo   Starting Parker DO-178C Platform 2.0
echo ===================================================

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10 or 3.11.
    pause
    exit /b 1
)

echo [2/3] Installing/Verifying dependencies...
pip install -r requirements.txt

echo [3/3] Launching FastAPI Web Application...
cd app\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
pause
