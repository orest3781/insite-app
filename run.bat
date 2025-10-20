@echo off
REM Previewless Insight Viewer Launcher for Windows
REM This script activates the virtual environment and runs the application

echo Starting Previewless Insight Viewer...
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to create the virtual environment.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the application
python main.py

REM Deactivate when done
deactivate

pause
