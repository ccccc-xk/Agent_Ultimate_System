# 05_企业级高级RAG知识库

企业级 RAG 调优系统，在项目四的基础上构建双路混合检索、Rerank 重排、Prompt 压缩、LangSmith 监控的完整知识库解决方案。

## 技术栈

- **Python 3.10+** + FastAPI
- **Elasticsearch 8.13** (BM25 关键词检索，IK 中文分词)
- **Milvus 2.4** (向量语义检索，COSINE 相似度)
- **BGE-Reranker-Large** (二次重排，通过 XInference 部署)
- **BGE-Large-ZH-v1.5** (1024 维 Embedding)
- **LangChain + LangSmith** (全链路 Tracing)
- **Qwen-Plus** (LLM，通过 DashScope)

## 系统架构

```
用户问题 → Hybrid Search (BM25 + Vector RRF) → Rerank (bge-reranker-large) → Context Compress → LLM 生成回答
```

详细架构图见 [系统架构](系统架构.md)

## 快速启动

### 1. 启动 Docker 服务

```bash
cd deploy
docker-compose up -d
```

这会启动：Elasticsearch (9200)、Milvus (19530)、XInference (9997)、etcd、MinIO

### 2. 初始化 Reranker 模型

```bash
# 等待 XInference 启动完成
python deploy/reranker/init_reranker.py
```

### 3. 配置环境变量

```bash
cp backend/.env.example backend/.env
# 编辑 .env，填入你的 API Key
```

### 4. 创建虚拟环境并安装依赖

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 5. 导入数据

```bash
# 导入到 Elasticsearch
python scripts/import_to_es.py

# 导入到 Milvus
python scripts/import_to_milvus.py
```

### 6. 启动 API 服务

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### 7. 一键启动 (Windows)

```bash
start.bat
```

## API 接口

### POST /api/rag/query

查询接口，供项目六 Dify 调用。

**请求：**
```json
{"question": "高血压怎么治疗？", "top_k": 3}
```

**响应：**
```json
{
  "answer": "高血压的治疗方法包括...",
  "sources": [
    {"doc_name": "常见疾病诊疗指南.md", "chunk_text": "...", "score": 0.87}
  ],
  "confidence": 0.87,
  "tokens_used": 1234,
  "elapsed_ms": 2500
}
```

### GET /api/rag/health

健康检查，返回 ES、Milvus、Reranker 服务状态。

## 评估与调参

```bash
# 运行评估（Hit Rate@3, MRR）
python eval/evaluate.py

# 运行参数调优（遍历权重组合）
python eval/evaluate.py --tune
```

评估报告输出到 `docs/benchmark_report.md` 和 `docs/tuning_report.md`。

## 项目结构

```
05_企业级高级RAG知识库/
├── backend/                    # 后端代码
│   ├── app/                    # 应用代码
│   │   ├── api/               # API 路由
│   │   ├── core/              # 核心模块 (检索/重排/压缩/生成)
│   │   ├── models/            # 数据模型
│   │   ├── loaders/           # 文档加载器
│   │   └── splitter/          # 文本分块器
│   ├── data/                  # 知识库文档
│   ├── eval/                  # 评估脚本和 QA 数据
│   ├── scripts/               # 数据导入脚本
│   └── requirements.txt
├── deploy/                     # Docker 部署
│   ├── docker-compose.yml     # ES + Milvus + XInference
│   ├── es/                    # ES Dockerfile (IK 插件)
│   └── reranker/              # Reranker 初始化脚本
├── docs/                       # 评估报告输出目录
│   ├── benchmark_report.md    # 性能基准（自动生成）
│   └── tuning_report.md       # 调参报告（自动生成）
├── 系统架构.md                 # 架构图
├── 模块说明.md                 # 模块说明
├── 配置参数说明.md             # 配置参数
├── 公司规章制度手册.md         # 知识库文档
├── 合同管理规范.md             # 知识库文档
├── README.md
├── start.bat                   # 一键启动
└── .gitignore
```

## 文档

- [系统架构](系统架构.md)
- [模块说明](模块说明.md)
- [配置参数](配置参数说明.md)
