@echo off
REM Medical RAG Backend Startup Script
REM All caches and models stored on D drive

set HF_ENDPOINT=https://hf-mirror.com
set HF_HOME=D:\Codex-project\Agent_Ultimate_System\04_医疗智能问诊基础RAG\.cache\huggingface
set SENTENCE_TRANSFORMERS_HOME=D:\Codex-project\Agent_Ultimate_System\04_医疗智能问诊基础RAG\.cache\sentence_transformers
set TORCH_HOME=D:\Codex-project\Agent_Ultimate_System\04_医疗智能问诊基础RAG\.cache\torch
set HF_HUB_DISABLE_XET=1

echo Starting Medical RAG Backend...
echo HF_HOME=%HF_HOME%
echo SENTENCE_TRANSFORMERS_HOME=%SENTENCE_TRANSFORMERS_HOME%
echo.

cd /d D:\Codex-project\Agent_Ultimate_System\04_医疗智能问诊基础RAG\backend
D:\Codex-project\Agent_Ultimate_System\04_医疗智能问诊基础RAG\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 9004
