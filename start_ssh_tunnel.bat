@echo off
title SSH Tunnel to Remote Ollama Server (Port 11434)
echo ===============================================================================
echo Establishing SSH Tunnel to Ollama Server (172.19.64.35:11434)...
echo Enter password 'root1' when prompted.
echo KEEP THIS WINDOW OPEN during your test case generation session.
echo ===============================================================================
ssh -L 11434:localhost:11434 root1@172.19.64.35
pause
