# 04_医疗智能问诊基础RAG

> 第四阶段——引入向量数据库，让系统拥有记忆与私有知识，实现无幻觉的医疗智能问答

---

## 项目架构

```
用户提问
   │
   ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Vue3 前端   │────▶│ FastAPI 后端  │────▶│  Milvus 向量  │
│  (ElementPlus)│◀────│  (LangChain) │◀────│   数据库      │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │                    ▲
                           ▼                    │
                    ┌──────────────┐     ┌──────────────┐
                    │  通义千问 LLM │     │  BGE-large-zh │
                    │  (Qwen API)  │     │  (Embedding)  │
                    └──────────────┘     └──────────────┘

知识库管理流程：
PDF/MD 上传 → 文档加载 → 文本切片(500字/overlap50) → BGE向量化 → Milvus存储
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python 3.10+ / FastAPI |
| AI 框架 | LangChain |
| LLM | 通义千问 Qwen（OpenAI 兼容接口） |
| Embedding | BGE-large-zh-v1.5（HuggingFace） |
| 向量数据库 | Milvus 2.4 Standalone |
| 前端框架 | Vue 3 + ElementPlus + Vite |
| 部署 | Docker + Docker Compose |

---

## 环境要求

- Python 3.10+
- Docker + Docker Compose
- Node.js 18+（前端开发时）
- GPU 可选（BGE 模型在 CPU 上也可运行，推理稍慢）
- 通义千问 API Key（[申请地址](https://dashscope.console.aliyun.com/)）

---

## 快速启动

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 2. Docker Compose 一键启动

```bash
docker-compose up -d
```

启动后访问：
- 前端界面：http://localhost:18080
- 后端 API 文档：http://localhost:8001/docs
- Milvus 管理：http://localhost:9091

### 3. 导入示例数据

```bash
# 进入后端容器
docker exec -it medical-rag-backend python -m app.core.data_import
```

---

## 本地开发

### 后端

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # 填入配置
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 普通对话 |
| POST | `/api/chat/stream` | 流式对话（SSE） |
| POST | `/api/knowledge/upload` | 上传文档 |
| GET | `/api/knowledge/list` | 知识库列表 |
| DELETE | `/api/knowledge/{doc_name}` | 删除文档 |
| GET | `/api/health` | 健康检查 |

---

## 测试用例

以下问答基于 `data/` 目录中的示例文档：

| # | 问题 | 预期结果 |
|---|------|---------|
| 1 | 高血压的诊断标准是什么？ | 返回收缩压/舒张压分级标准（140/90mmHg起） |
| 2 | 阿莫西林怎么吃？一次几粒？ | 返回成人每次0.5g（2粒），每6-8小时一次 |
| 3 | 头晕应该看哪个科室？ | 建议就诊神经内科 |
| 4 | 糖尿病患者饮食要注意什么？ | 返回低GI食物、控制热量、定时定量等建议 |
| 5 | 量子纠缠是怎么回事？ | 与医疗无关，返回兜底提示"建议前往医院就诊" |

---

## 项目目录

```
04_医疗智能问诊基础RAG/
├── backend/                  # FastAPI 后端
│   ├── app/
│   │   ├── api/              # API 路由（chat, knowledge）
│   │   ├── core/             # 核心模块（embedding, milvus, llm, rag）
│   │   ├── loaders/          # 文档加载器（PDF, Markdown）
│   │   ├── splitter/         # 文本切片器
│   │   └── models/           # Pydantic 数据模型
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── views/            # 页面（Chat, Knowledge）
│   │   ├── components/       # 组件（SourceCard）
│   │   ├── api/              # 接口层
│   │   └── router/           # 路由
│   ├── Dockerfile
│   └── nginx.conf
├── data/                     # 示例医疗知识文档
├── docker-compose.yml
└── README.md
```
