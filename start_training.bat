@echo off
title Jessica AI - Continuous Training
color 0e
echo ===================================================
echo   JESSICA AI - CONTINUOUS TRAINING MODULE
echo ===================================================
echo.
echo [INFO] This module runs independently to learn from the web.
echo [INFO] It will not interfere with the main application.
echo.

set PYTHONPATH=%CD%
python src/backend/continuous_learning.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Training module stopped.
    pause
)
