@echo off
REM Setup script for Previewless Insight Viewer
REM Creates virtual environment and installs dependencies

echo ========================================
echo Previewless Insight Viewer Setup
echo ========================================
echo.

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To run the application:
echo   1. Run "run.bat"
echo   OR
echo   2. Activate venv: venv\Scripts\activate.bat
echo      Run app: python main.py
echo.

pause
