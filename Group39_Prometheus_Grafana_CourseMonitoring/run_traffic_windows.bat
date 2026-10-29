@echo off
cd /d "%~dp0"
set MODE=%1
if "%MODE%"=="" set MODE=mixed
python scripts\generate_traffic.py --mode %MODE% --duration 90 --rps 10
pause
