@echo off
title FraudLens AI - Frontend Web App
cd /d "%~dp0frontend"
echo ====================================================
echo Starting FraudLens AI Frontend on port 5173...
echo ====================================================
echo.
call npm.cmd run dev
pause
