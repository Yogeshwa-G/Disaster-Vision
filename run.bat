@echo off
setlocal
cd /d "%~dp0"
echo ================================================================
echo DisasterVision - POPUP FIX EDITION
echo ================================================================
echo.
echo Stopping old DisasterVision processes on ports 8107 and 5537...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8107" ^| findstr "LISTENING"') do taskkill /F /PID %%P >nul 2>&1
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5537" ^| findstr "LISTENING"') do taskkill /F /PID %%P >nul 2>&1
echo Checking Python packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Could not install the required package.
  pause
  exit /b 1
)
echo.
echo Starting DisasterVision...
echo Open this exact address: http://127.0.0.1:8107
echo If the page was already open, press Ctrl+F5 after launch.
echo.
python client.py
pause
