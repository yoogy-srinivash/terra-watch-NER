@echo off
title TerraWatch NER - Master Launcher
cls
echo =====================================================================
echo    TERRAWATCH NER - AI EARLY WARNING & RISK MONITORING
echo    Academic Multi-Modal AI Research Prototype (North Eastern Region)
echo =====================================================================
echo.

cd /d "%~dp0"

if not exist ".env" (
    if exist ".env.example" (
        echo  - Creating .env configuration from .env.example...
        copy ".env.example" ".env" >nul
    )
)

echo [1/3] Checking FastAPI Backend Server...
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo  - Backend Server is ALREADY running on port 8000.
) else (
    echo  - Starting FastAPI Backend Server on http://localhost:8000 ...
    start "TerraWatch Backend Server" cmd /k ".\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload"
    timeout /t 3 /nobreak >nul
)

echo.
echo [2/3] Opening TerraWatch Portal in your default browser...
start "" "http://localhost:8000/ui/index.html"
start "" "http://localhost:8000/ui/login.html"

echo.
echo [3/3] System Ready!
echo =====================================================================
echo    PORTAL SHORTCUTS:
echo =====================================================================
echo    1. Overview Dashboard:  http://localhost:8000/ui/index.html
echo    2. Sign In / Switch:    http://localhost:8000/ui/login.html
echo    3. Live GIS Risk Map:   http://localhost:8000/ui/live-risk-map.html
echo    4. AI Risk Lab:         http://localhost:8000/ui/probability-risk.html
echo    5. Admin Operations:    http://localhost:8000/ui/admin.html
echo    6. API Docs (Swagger):  http://localhost:8000/docs
echo =====================================================================
echo.
echo Would you like to start the IoT Sensor Simulator to stream live telemetry?
set /p run_sim="Start IoT Sensor Simulator? (Y/N, default Y): "
if "%run_sim%"=="" set run_sim=Y
if /i "%run_sim%"=="Y" (
    echo Starting IoT Sensor Simulator...
    start "TerraWatch IoT Simulator" cmd /k ".\venv\Scripts\python.exe sensor_simulator/sensor_simulator.py --backend-url http://localhost:8000 --interval 5"
)

echo.
echo All components are active and connected!
pause
