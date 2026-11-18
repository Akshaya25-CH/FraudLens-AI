@echo off
title FraudLens AI - Backend Server
cd /d "%~dp0"
echo ====================================================
echo Starting FraudLens AI Backend Server on port 8000...
echo ====================================================
echo.
backend\venv\Scripts\python.exe backend\main.py
pause
