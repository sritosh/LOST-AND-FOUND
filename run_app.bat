@echo off
cd /d "%~dp0"
title Campus Lost and Found System - DBMS Project
echo ========================================================
echo   CAMPUS LOST AND FOUND SYSTEM - DBMS LAB PROJECT
echo   Team: Sritosh Rath (24BDS0001) ^& Jayant Sharma (24BAI0148)
echo   Milestone: Review 1 (50%% Progress Demonstration)
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% equ 0 (
    python run_app.py
    goto end
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    py run_app.py
    goto end
)

where python3 >nul 2>nul
if %errorlevel% equ 0 (
    python3 run_app.py
    goto end
)

echo [ERROR] Python was not found in your system PATH!
echo Please install Python or check your PATH environment variable.
echo.

:end
pause

