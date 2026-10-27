@echo off
title TerraWatch NER - IoT Sensor & Soil Moisture Simulator
echo =====================================================================
echo    TERRAWATCH NER - IOT TELEMETRY SIMULATOR (8 NER STATES)
echo    Pushing real-time soil moisture, pore pressure and vibration...
echo =====================================================================
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --backend-url http://localhost:8000 --interval 6 --iterations 0 --hazard-station SN-ML-001
pause
