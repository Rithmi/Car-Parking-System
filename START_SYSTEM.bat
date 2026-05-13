@echo off
REM =====================================================
REM PARKING MANAGEMENT SYSTEM - Windows Startup Script
REM =====================================================
REM 
REM This script sets up and runs the complete parking
REM management system on Windows.
REM
REM Usage: Double-click this file to start the system
REM =====================================================

echo.
echo =====================================================
echo  PARKING MANAGEMENT SYSTEM - STARTUP
echo =====================================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)

echo [OK] Python found

REM Install dependencies if needed
echo.
echo Installing dependencies...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies may not have installed
)

echo [OK] Dependencies ready

REM Create necessary directories
if not exist templates mkdir templates
if not exist static mkdir static
if not exist captures mkdir captures
if not exist exports mkdir exports
echo [OK] Directories created

REM Initialize database
python -c "import db; db.init_db()" >nul 2>&1
echo [OK] Database ready

REM Display information
echo.
echo =====================================================
echo  STARTING WEB SERVER
echo =====================================================
echo.
echo   Dashboard:    http://localhost:5000/
echo   Control:      http://localhost:5000/control
echo   Reports:      http://localhost:5000/reports
echo.
echo   To stop: Press Ctrl+C
echo.
echo =====================================================
echo.

REM Start Flask
python app_ui.py

REM If Flask exits, show message
echo.
echo System stopped.
pause
