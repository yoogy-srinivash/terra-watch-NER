@echo off
title TerraWatch NER - UI Portal
echo =====================================================================
echo    TERRAWATCH NER - WEB DASHBOARD PORTAL
echo    Opening TerraWatch NER UI in your default web browser...
echo =====================================================================
echo.

start "" "http://localhost:8000/ui/index.html"
echo Dashboard launched at: http://localhost:8000/ui/index.html
echo Live Risk Map at:      http://localhost:8000/ui/live-risk-map.html
echo Admin Portal at:       http://localhost:8000/ui/admin.html
echo API Interactive Docs:  http://localhost:8000/docs
echo.
pause
