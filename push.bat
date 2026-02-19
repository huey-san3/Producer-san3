@echo off
title SAN3 — Push to GitHub
echo.
echo  SAN3 PRODUCER — Push to GitHub
echo  ================================
echo.

REM Check git is installed
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: git not found. Install from https://git-scm.com
    pause
    exit /b 1
)

REM Show what will be pushed
echo  Changes to push:
git status --short
echo.

REM Stage everything
git add -A

REM Get commit message
set /p MSG="  Commit message (or press ENTER for 'update'): "
if "%MSG%"=="" set MSG=update

REM Commit
git commit -m "%MSG%"

REM Push
echo.
echo  Pushing to GitHub...
git push origin main

if %errorlevel% equ 0 (
    echo.
    echo  Done. Live at: https://github.com/huey-san3/Producer-san3
) else (
    echo.
    echo  Push failed. Run: gh auth login
    echo  Or set up credentials at: https://github.com/settings/tokens
)

echo.
pause
