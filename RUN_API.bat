@echo off
cd /d "%~dp0"
title FlowAI API
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
pause
