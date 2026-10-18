@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo First run INSTALL_WINDOWS.bat to install the project.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m streamlit run dashboard\app.py
pause
