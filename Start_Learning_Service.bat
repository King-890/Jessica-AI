@echo off
title Jessica AI - Autonomous Learning Service
color 0B
echo ===================================================
echo   STARTING JESSICA AI AUTONOMOUS LEARNER
echo   (Background Service - Runs 24/7)
echo ===================================================
echo[
echo This service will:
echo 1. Connect to Supabase
echo 2. Research new topics
echo 3. Archive knowledge
echo[
echo To stop, close this window.
echo[

:: Set Python Path
set PYTHONPATH=%CD%

:: Run the script
python src/backend/continuous_learning.py --duration 0

pause
