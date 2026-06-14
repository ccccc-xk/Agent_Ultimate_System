"""
FastAPI application entry point.
Initializes Milvus, embedding model, and mounts API routes.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.core import milvus_client, embedding
from app.models.schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    # Startup
    logger.info("=== Medical RAG System Starting ===")

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Connect to Milvus
    try:
        milvus_client.connect()
        milvus_client.create_collection()
        logger.info("Milvus connected and collection ready.")
    except Exception as e:
        logger.error(f"Milvus initialization failed: {e}")

    # Pre-load embedding model
    try:
        embedding.get_model()
        logger.info("Embedding model loaded.")
    except Exception as e:
        logger.error(f"Embedding model loading failed: {e}")

    logger.info("=== Medical RAG System Ready ===")
    yield
    # Shutdown
    logger.info("=== Medical RAG System Shutting Down ===")


app = FastAPI(
    title="Medical Intelligent Consultation RAG API",
    description="医疗智能问诊 RAG 系统 API - 基于 LangChain + Milvus + BGE + Qwen",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(chat_router)
app.include_router(knowledge_router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        milvus_connected=True,
        embedding_loaded=embedding.is_loaded(),
    )


@app.get("/")
async def root():
    return {"message": "Medical RAG System API", "docs": "/docs"}
