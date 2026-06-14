# 部署指南 - Vercel + Render

## 架构总览

```
┌─ Vercel (免费) ──────────────────────┐
│  • Landing Page (index.html)          │
│  • P01 企业管理前端 (Vue 3)            │
│  • P02 物流管理前端 (Vue 3)            │
│  • P04 医疗问诊前端 (Vue 3)            │
│  • P06 Agent 聊天展示页 (HTML/JS)      │
└───────────────────────────────────────┘
         ↕ API 调用
┌─ Render (免费/付费) ──────────────────┐
│  • P01 Spring Boot API                │
│  • P02 Spring Boot API                │
│  • P04 FastAPI Medical RAG            │
│  • PostgreSQL (免费 90天)              │
└───────────────────────────────────────┘
         ↕ 工具调用
┌─ 外部服务 ────────────────────────────┐
│  • Dify Cloud (cloud.dify.ai)         │
│  • DeepSeek API                       │
│  • Zilliz Cloud (托管 Milvus)         │
└───────────────────────────────────────┘
```

## 部署步骤

### 第一步：推送到 GitHub

```bash
cd D:\Codex-project\Agent_Ultimate_System
git init
git add .
git commit -m "feat: prepare for Vercel + Render deployment"
git remote add origin https://github.com/YOUR_USERNAME/agent-ultimate-system.git
git push -u origin main
```

### 第二步：部署前端到 Vercel

1. 登录 [vercel.com](https://vercel.com)
2. 点击 "New Project" → 导入 GitHub 仓库
3. **Landing Page（主入口）**:
   - Framework Preset: Other
   - Root Directory: `.` (项目根目录)
   - Build Command: (留空)
   - Output Directory: `.`
   - 部署后获得 URL: `https://xxx.vercel.app`

4. **P01 企业管理前端**:
   - 新建 Project，Root Directory: `01_企业管理基座系统/frontend`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - 环境变量: `VITE_API_BASE` = `https://p01-backend.onrender.com`

5. **P02 物流前端**:
   - Root Directory: `02_政企物流智能化转化/frontend`
   - Framework Preset: Vite
   - 环境变量: `VITE_API_BASE` = `https://p02-backend.onrender.com`

6. **P06 Agent 展示页**:
   - Root Directory: `06_Agent智能体合流总管/frontend`
   - Framework Preset: Other
   - Output Directory: `.`
   - 在 index.html 中填入 Dify Cloud 的 API 地址和 Key

### 第三步：部署后端到 Render

1. 登录 [render.com](https://render.com)
2. 连接 GitHub 仓库
3. 使用 Blueprint 一键部署 (render.yaml)，或手动创建：

**P01 Backend**:
- Runtime: Java
- Build Command: `cd "01_企业管理基座系统/backend" && mvn clean package -DskipTests`
- Start Command: `cd "01_企业管理基座系统/backend" && java -jar target/enterprise-base-1.0.0.jar`
- 环境变量:
  - `DB_URL` = 你的 MySQL 连接字符串
  - `DB_USERNAME` = 数据库用户名
  - `DB_PASSWORD` = 数据库密码
  - `AI_API_KEY` = DeepSeek API Key
  - `AI_API_URL` = `https://api.deepseek.com/v1/chat/completions`
  - `AI_MODEL` = `deepseek-chat`

**P02 Backend**:
- Runtime: Java
- Build Command: `cd "02_政企物流智能化转化/backend" && mvn clean package -DskipTests`
- Start Command: `cd "02_政企物流智能化转化/backend" && java -jar target/smart-logistics-1.0.0.jar`
- 环境变量同上 + `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`

**P04 Backend** (需要 Starter 计划 $7/月):
- Runtime: Python
- Build Command: `cd "04_医疗智能问诊基础RAG/backend" && pip install -r requirements.txt`
- Start Command: `cd "04_医疗智能问诊基础RAG/backend" && uvicorn app.main:app --host 0.0.0.0 --port 10000`
- 环境变量:
  - `OPENAI_API_KEY` = DeepSeek API Key
  - `OPENAI_BASE_URL` = `https://api.deepseek.com/v1`
  - `MILVUS_HOST` = Zilliz Cloud 地址
  - `MILVUS_PORT` = Zilliz Cloud 端口

### 第四步：配置数据库

**方案 A：Render PostgreSQL（免费 90 天）**
- 在 Render Dashboard 创建 PostgreSQL 数据库
- 将 MySQL 表结构迁移到 PostgreSQL（改动不大）

**方案 B：外部 MySQL 服务（推荐长期方案）**
- [TiDB Cloud](https://tidbcloud.com/) 免费 5GB
- [Aiven](https://aiven.io/) 免费 MySQL
- [PlanetScale](https://planetscale.com/) 免费 Hobby

### 第五步：配置 Dify Cloud

1. 注册 [cloud.dify.ai](https://cloud.dify.ai)
2. 创建 Agent 应用
3. 添加 DeepSeek 模型
4. 导入 `06_Agent智能体合流总管/openapi/` 下的工具定义
5. 将工具 URL 改为 Render 部署地址
6. 发布应用，获取 API Key

### 第六步：回填 URL

将各平台获得的 URL 回填到对应配置中：
1. Vercel 前端的 `VITE_API_BASE` 环境变量
2. Dify 工具定义中的服务器 URL
3. Landing Page 中的链接

## 注意事项

- Render 免费实例 15 分钟无请求会休眠，首次访问冷启动 30-60 秒
- P04/P05 的 embedding 模型 (BGE-large) 需要较大内存，建议至少 Starter 计划
- MySQL 密码等敏感信息不要提交到 Git，使用环境变量
- DeepSeek API 按量计费，非常便宜（约 ¥1/百万 token）
