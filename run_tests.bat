@echo off
title TerraWatch NER - Automated Test Suite
echo =====================================================================
echo    TERRAWATCH NER - RUNNING AUTOMATED VERIFICATION SUITES
echo =====================================================================
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe -m pytest backend/tests/test_api.py -v
pause
