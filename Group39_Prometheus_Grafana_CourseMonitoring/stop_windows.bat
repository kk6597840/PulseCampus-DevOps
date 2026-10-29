@echo off
cd /d "%~dp0"
docker compose down
echo Stopped. The database and metrics history are preserved.
pause
