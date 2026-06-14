@echo off
chcp 65001 >nul
echo ============================================
echo   Agent 智能体合流总管 — 一键启动所有服务
echo ============================================
echo.

set BASE=D:\Codex-project\Agent_Ultimate_System

:: 检查 Docker 是否运行
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)

:: 启动 Dify (项目六)
echo [1/7] 启动 Dify Agent 平台 (端口 9006)...
cd /d D:\dify\docker
docker compose up -d
echo       Dify 启动中...

:: 等待 Dify
echo [2/7] 等待 Dify 就绪 (20秒)...
ping -n 21 127.0.0.1 >nul

:: 启动项目一 (后端+前端)
echo [3/7] 启动项目一 企业管理 (后端:9001 前端:5173)...
start "P01-All" cmd /c "cd /d "%BASE%\01_企业管理基座系统" && call 启动系统.bat"
echo       已启动

:: 启动项目二
echo [4/7] 启动项目二 NLP派单 (后端:9002 前端:5174)...
start "P02-All" cmd /c "cd /d "%BASE%\02_政企物流智能化转化" && call start.bat"
echo       已启动

:: 启动项目四
echo [5/7] 启动项目四 医疗RAG (端口 9004)...
start "P04" cmd /c "cd /d "%BASE%\04_医疗智能问诊基础RAG" && call 启动系统.bat"
echo       已启动

:: 启动项目五
echo [6/7] 启动项目五 企业RAG (端口 9005)...
start "P05" cmd /c "cd /d "%BASE%\05_企业级高级RAG知识库" && call start.bat"
echo       已启动

echo [7/7] 等待所有服务就绪 (15秒)...
ping -n 16 127.0.0.1 >nul

echo.
echo ============================================
echo   所有服务启动完成！
echo.
echo   P01 企业管理前端 : http://localhost:5173  (admin/123456)
echo   P02 NLP派单前端   : http://localhost:5174
echo   P04 医疗RAG文档   : http://localhost:9004/docs
echo   P05 企业RAG文档   : http://localhost:9005/docs
echo   P06 Dify 管理台   : http://localhost:9006  (2257302877@qq.com)
echo   P06 Agent 聊天    : http://localhost:9006/chat/QE5z5H48rYoZMabr
echo ============================================
echo.
echo 打开 Agent 聊天页面...
start http://localhost:9006/chat/QE5z5H48rYoZMabr
