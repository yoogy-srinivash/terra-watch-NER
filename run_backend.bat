@echo off
title TerraWatch NER - FastAPI Backend Server
echo =====================================================================
echo    TERRAWATCH NER - AI EARLY WARNING & RISK MONITORING
echo    Starting FastAPI Backend Engine with ML Pipeline & Geospatial SQLite
echo =====================================================================
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
