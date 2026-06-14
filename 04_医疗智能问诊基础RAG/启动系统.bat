@echo off
chcp 65001 >nul
title Medical RAG System

echo ============================================
echo    Medical RAG - Startup
echo ============================================
echo.

:: Check Python venv
if not exist "%~dp0backend\.venv\Scripts\python.exe" (
    echo [ERROR] Python venv not found at backend\.venv
    pause
    exit /b 1
)

:: Check Docker (Milvus)
echo [1/3] Checking Milvus...
docker ps --format "{{.Names}}" 2>nul | findstr "milvus" >nul
if errorlevel 1 (
    echo [WARN] Milvus container not running. Starting...
    docker start medical-rag-milvus 2>nul
    timeout /t 5 /nobreak >nul
)

:: Start Backend
echo [2/3] Starting Backend (port 9004)...
cd /d "%~dp0backend"
start "MedicalRAG-9004" /min cmd /c "set HF_ENDPOINT=https://hf-mirror.com && set HF_HOME=%~dp0.cache\huggingface && set SENTENCE_TRANSFORMERS_HOME=%~dp0.cache\sentence_transformers && set TORCH_HOME=%~dp0.cache\torch && set HF_HUB_DISABLE_XET=1 && ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9004"

:: Wait for backend
echo [3/3] Waiting for backend...
set /a count=0
:waitloop
timeout /t 3 /nobreak >nul
set /a count+=3
curl -s http://localhost:9004/api/health 2>nul | findstr "ok" >nul
if not errorlevel 1 (
    echo [OK] Backend is ready
    goto ready
)
if %count% lss 60 (
    echo     ... waiting (%count%s^)
    goto waitloop
)
echo [WARN] Backend may still be loading embedding model...

:ready
echo.
echo ============================================
echo    Medical RAG is ready!
echo    API Docs:  http://localhost:9004/docs
echo    Health:    http://localhost:9004/api/health
echo ============================================
echo.
echo Opening browser...
start http://localhost:9004/docs
echo.
echo Press any key to STOP all services...
pause >nul

echo Stopping services...
taskkill /f /fi "WINDOWTITLE eq MedicalRAG-9004" >nul 2>&1
echo Done.
