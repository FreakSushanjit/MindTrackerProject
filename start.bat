@echo off
title VoiceMind Launcher
echo ===================================================
echo           Starting VoiceMind Application
echo ===================================================
echo.

:: Detect Python executable with required dependencies
set "PY_CMD="

if exist "D:\Anaconda\python.exe" (
    set "PY_CMD=D:\Anaconda\python.exe"
) else if exist "%~dp0Backend\venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0Backend\venv\Scripts\python.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0venv\Scripts\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else (
    set "PY_CMD=python"
)

echo Using Python: %PY_CMD%
echo.

:: Launch Backend in its own window
start "VoiceMind Backend (FastAPI)" cmd /k "cd /d %~dp0Backend && "%PY_CMD%" -m uvicorn app.main:app --reload --port 8000"

:: Launch Frontend in its own window
start "VoiceMind Frontend (Vite)" cmd /k "cd /d %~dp0Frontend && npm run dev"

echo Backend starting at:  http://localhost:8000
echo Frontend starting at: http://localhost:5173
echo.
echo Servers have been launched in separate terminal windows.
echo Keep those windows open while using the application.
echo ===================================================
timeout /t 5 >nul
