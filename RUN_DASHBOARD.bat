@echo off
cd /d "%~dp0"
title FlowAI Dashboard
if not exist .venv\Scripts\python.exe (
  echo Virtual environment not found. Run INSTALL_WINDOWS.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run dashboard\app.py
pause
