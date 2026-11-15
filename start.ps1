# VoiceMind Startup Script for PowerShell
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "          Starting VoiceMind Application           " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Locate Python executable that has dependencies
$pythonPath = "python"
$candidatePaths = @(
    "D:\Anaconda\python.exe",
    "$projectRoot\Backend\venv\Scripts\python.exe",
    "$projectRoot\venv\Scripts\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
)

foreach ($candidate in $candidatePaths) {
    if (Test-Path $candidate) {
        $pythonPath = $candidate
        break
    }
}

Write-Host "Using Python: $pythonPath" -ForegroundColor Yellow

# Start Backend in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\Backend'; & '$pythonPath' -m uvicorn app.main:app --reload --port 8000"

# Start Frontend in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\Frontend'; npm run dev"

Write-Host ""
Write-Host "Backend:  http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Servers launched in separate terminal windows." -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan
