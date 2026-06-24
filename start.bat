@echo off
echo ====================================
echo AI SOC Assistant - Quick Start
echo ====================================
echo.

echo [1/4] Checking Node.js...
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js 20+
    pause
    exit /b 1
)
node --version

echo.
echo [2/4] Checking Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)
python --version

echo.
echo [3/4] Starting Backend Server...
start "AI SOC Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Starting Frontend Server...
start "AI SOC Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ====================================
echo Servers Starting!
echo ====================================
echo.
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:3000
echo.
echo Press any key to open frontend in browser...
pause >nul
start http://localhost:3000

echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
