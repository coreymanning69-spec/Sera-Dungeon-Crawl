@echo off
title SERA: ENDLESS ENGAGEMENT
cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel%==0 (
    python play.py
    pause
    exit /b
)

where python3 >nul 2>nul
if %errorlevel%==0 (
    python3 play.py
    pause
    exit /b
)

where py >nul 2>nul
if %errorlevel%==0 (
    py play.py
    pause
    exit /b
)

echo.
echo  ERROR: Python not found!
echo.
echo  To play SERA, you need Python installed.
echo  Download it from: https://www.python.org/downloads/
echo  During install, CHECK the box that says "Add Python to PATH"
echo.
pause
