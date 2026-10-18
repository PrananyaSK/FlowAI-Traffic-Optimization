@echo off
setlocal
cd /d "%~dp0"
title FlowAI - Install Dependencies
echo ======================================================
echo FlowAI Traffic Command Center - Windows Setup
echo ======================================================
where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11 from python.org and enable Add Python to PATH.
  pause
  exit /b 1
)
if not exist .venv (
  py -3.11 -m venv .venv
  if errorlevel 1 (
    echo Python 3.11 was not found. Please install Python 3.11 and retry.
    pause
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto failed
python -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo.
echo Setup complete. Double-click RUN_DASHBOARD.bat to launch FlowAI.
pause
exit /b 0
:failed
echo.
echo Installation failed. Read the error above. Python 3.11 x64 is recommended.
pause
exit /b 1
