"""
FastAPI application entry point.
Handles startup initialization (ES, Milvus, Embedding model).
"""

import os
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Load .env file
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"Loaded .env from {env_path}")
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("=== Starting Enterprise RAG System ===")

    # 1. Initialize Elasticsearch
    try:
        from app.core import bm25_search
        bm25_search.ensure_index()
        es_count = bm25_search.index_count()
        logger.info(f"Elasticsearch ready. Index '{settings.ES_INDEX}': {es_count} docs")

        # Auto-import if index is empty
        if es_count == 0:
            logger.info("ES index is empty. Running data import...")
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            if os.path.exists(data_dir):
                from scripts.import_to_es import import_to_es
                import_to_es(data_dir)
    except Exception as e:
        logger.error(f"Elasticsearch init failed: {e}")

    # 2. Initialize Milvus
    try:
        from app.core import vector_search
        vector_search.ensure_initialized()
        logger.info("Milvus connected and collection loaded.")
    except Exception as e:
        logger.error(f"Milvus init failed: {e}")

    # 3. Pre-load Embedding model
    try:
        from app.core import embedding
        embedding.get_model()
        logger.info("Embedding model loaded.")
    except Exception as e:
        logger.error(f"Embedding model init failed: {e}")

    # 4. Check Reranker service
    try:
        from app.core import reranker as reranker_mod
        status = reranker_mod.check_reranker_health()
        logger.info(f"Reranker status: {status['status']}")
    except Exception as e:
        logger.error(f"Reranker check failed: {e}")

    logger.info("=== Enterprise RAG System Ready ===")
    yield
    logger.info("=== Shutting down ===")


app = FastAPI(
    title="Enterprise Advanced RAG API",
    description="企业级高级RAG知识库 - Hybrid Search + Rerank + Context Compression",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
from app.api.rag import router as rag_router
app.include_router(rag_router)


@app.get("/")
def root():
    return {
        "service": "Enterprise Advanced RAG",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "query": "POST /api/rag/query",
            "health": "GET /api/rag/health",
        },
    }
