@echo off
title Jessica AI - Engineering Console
color 0b

echo ===================================================
echo      STARTING JESSICA AI ENGINEERING CONSOLE
echo ===================================================
echo.

cd /d "%~dp0.."

echo [INFO] Setting PYTHONPATH...
set PYTHONPATH=%CD%

echo [INFO] Checking environment...
:: Add virtualenv check here if needed in future

echo [INFO] Launching Application...
echo.

python src/main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application crashed or closed with error.
    pause
)
