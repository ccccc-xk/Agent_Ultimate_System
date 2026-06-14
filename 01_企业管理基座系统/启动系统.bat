@echo off
chcp 65001 >nul
title Enterprise Management System

echo ============================================
echo    Enterprise Base System - Startup
echo ============================================
echo.

:: Kill ALL existing java and node processes (simple and reliable)
echo [0/4] Cleaning up old processes...
taskkill /f /im java.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Old processes cleaned

:: Check Java
set JAVA_HOME=D:\Program Files\Java\jdk-17
if not exist "%JAVA_HOME%\bin\java.exe" (
    echo [ERROR] JDK not found at %JAVA_HOME%
    pause
    exit /b 1
)

:: Check Node
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found
    pause
    exit /b 1
)

:: Check MySQL
sc query MySQL80 >nul 2>&1
if errorlevel 1 (
    echo [WARN] MySQL service may not be running. Make sure MySQL is started.
)

:: Check jar exists
if not exist "%~dp0backend\target\enterprise-base-1.0.0.jar" (
    echo [ERROR] Backend JAR not found. Please build first.
    pause
    exit /b 1
)

echo [1/4] Starting Backend...
cd /d "%~dp0backend"
start "Backend-9001" /min cmd /c "set JAVA_HOME=D:\Program Files\Java\jdk-17 && "%JAVA_HOME%\bin\java" -jar target\enterprise-base-1.0.0.jar"

:: Wait for backend health check
echo [2/4] Waiting for backend to be ready...
set /a count=0
:waitloop
timeout /t 2 /nobreak >nul
set /a count+=2
curl -s -o nul -w "%{http_code}" http://localhost:9001/api/auth/login -X POST -H "Content-Type: application/json" -d "{\"username\":\"admin\",\"password\":\"123456\"}" 2>nul | findstr "200" >nul
if not errorlevel 1 (
    echo [OK] Backend is ready
    goto backend_ready
)
if %count% lss 40 (
    echo     ... waiting (%count%s^)
    goto waitloop
)
echo [WARN] Backend may still be starting, continuing...
:backend_ready

echo [3/4] Starting Frontend...
cd /d "%~dp0frontend"
start "Frontend-5173" /min cmd /c "npx vite --port 5173 --strictPort"

:: Wait for frontend to start
echo [4/4] Waiting for frontend...
timeout /t 6 /nobreak >nul

:: Verify frontend is up
curl -s -o nul -w "%{http_code}" http://localhost:5173 2>nul | findstr "200" >nul
if errorlevel 1 (
    echo [WARN] Frontend may still be starting...
    timeout /t 5 /nobreak >nul
)

echo.
echo ============================================
echo    System is ready!
echo    Frontend: http://localhost:5173
echo    Backend:  http://localhost:9001
echo    Account:  admin / 123456
echo ============================================
echo.
echo Opening browser...
start http://localhost:5173
echo.
echo Press any key to STOP all services...
pause >nul

:: Cleanup
echo Stopping services...
taskkill /f /im java.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1
echo All services stopped.
timeout /t 2 /nobreak >nul
