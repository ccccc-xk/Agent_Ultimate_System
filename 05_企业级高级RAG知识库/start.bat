@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   05 Enterprise Advanced RAG - Starting...
echo ============================================

REM Start Docker services
cd /d "%~dp0deploy"
echo.
echo [1/7] Starting Docker containers...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Docker start failed. Is Docker Desktop running?
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Wait for services
echo.
echo [2/7] Waiting 30s for services to start...
timeout /t 30 /nobreak >nul

REM Initialize Reranker model
echo.
echo [3/7] Initializing Reranker model...
cd /d "%~dp0"
python deploy\reranker\init_reranker.py
if errorlevel 1 (
    echo WARNING: Reranker init failed, will try again later.
)

REM Create virtual environment if not exists
echo.
echo [4/7] Setting up Python environment...
if not exist "backend\.venv" (
    echo Creating virtual environment on D drive...
    python -m venv backend\.venv
)
call backend\.venv\Scripts\activate.bat

REM Install dependencies
echo.
echo [5/7] Installing dependencies...
pip install -r backend\requirements.txt -q

REM Copy .env if not exists
if not exist "backend\.env" (
    copy "backend\.env.example" "backend\.env" >nul
    echo.
    echo NOTE: Please edit backend\.env with your API keys.
)

REM Import data to ES and Milvus
echo.
echo [6/7] Importing documents to Elasticsearch...
cd /d "%~dp0backend"
python scripts\import_to_es.py

echo.
echo [7/7] Importing documents to Milvus...
python scripts\import_to_milvus.py

REM Start backend
echo.
echo ============================================
echo   Starting API server on port 9005...
echo   API docs: http://localhost:9005/docs
echo ============================================
python -m uvicorn app.main:app --host 0.0.0.0 --port 9005 --reload
