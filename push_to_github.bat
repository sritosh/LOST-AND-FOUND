@echo off
cd /d "%~dp0"
title Push to GitHub - Campus Lost and Found
echo ========================================================
echo   PUSHING TO GITHUB: sritosh/CAMPUS-LOST_FOUND
echo ========================================================
echo.
git remote set-url origin https://github.com/sritosh/CAMPUS-LOST_FOUND.git
git branch -M main
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo  [SUCCESS] Repository successfully pushed to GitHub!
    echo  View at: https://github.com/sritosh/CAMPUS-LOST_FOUND
    echo ========================================================
) else (
    echo ========================================================
    echo  [NOTE] If authentication failed:
    echo  1. Create a Personal Access Token at:
    echo     https://github.com/settings/tokens
    echo  2. Check the 'repo' permission checkbox.
    echo  3. Use token as password when prompted.
    echo ========================================================
)
echo.
pause
