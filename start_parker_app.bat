@echo off
title Parker AI Verification Tool Server (Port 8080)
echo ===============================================================================
echo Starting DO-178C AI Parker Test Case Generator Tool...
echo Server URL: http://localhost:8080
echo ===============================================================================
cd app\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080
pause
