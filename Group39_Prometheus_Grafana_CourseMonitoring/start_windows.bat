@echo off
cd /d "%~dp0"
echo Starting Group 39 monitoring project...
docker compose up --build -d
if errorlevel 1 (
 echo ERROR: Start Docker Desktop, then run this file again.
 pause
 exit /b 1
)
echo.
echo Student app: http://localhost:5000
echo Prometheus : http://localhost:9090/targets
echo Grafana    : http://localhost:3000 ^(admin / group39demo unless changed^)
echo.
echo See docs\DEMO_GUIDE.md for a live demonstration.
pause
