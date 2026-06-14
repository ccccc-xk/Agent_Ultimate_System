@echo off
chcp 65001 >nul
title Stop Services

echo ============================================
echo    Stopping Enterprise System...
echo ============================================
echo.

echo Stopping Java (Backend)...
taskkill /f /im java.exe >nul 2>&1
if errorlevel 1 (
    echo [OK] No Java process found
) else (
    echo [OK] Java stopped
)

echo Stopping Node (Frontend)...
taskkill /f /im node.exe >nul 2>&1
if errorlevel 1 (
    echo [OK] No Node process found
) else (
    echo [OK] Node stopped
)

echo.
echo ============================================
echo    All services stopped.
echo ============================================
timeout /t 3 /nobreak >nul
