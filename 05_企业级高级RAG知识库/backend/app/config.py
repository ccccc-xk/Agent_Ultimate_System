from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration (OpenAI-compatible, e.g. Qwen via DashScope)
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL_NAME: str = "qwen-plus"

    # Milvus Configuration
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "enterprise_knowledge"

    # Elasticsearch Configuration
    ES_HOST: str = "http://localhost:9200"
    ES_INDEX: str = "enterprise_knowledge"

    # Embedding Configuration
    EMBEDDING_MODEL_PATH: str = "BAAI/bge-large-zh-v1.5"
    EMBEDDING_DIMENSION: int = 1024

    # Reranker Configuration
    RERANKER_MODEL_PATH: str = "BAAI/bge-reranker-large"
    RERANKER_THRESHOLD: float = 0.6

    # RAG Configuration
    TOP_K: int = 3
    BM25_WEIGHT: float = 0.4
    VECTOR_WEIGHT: float = 0.6
    RRF_K: int = 60
    SIMILARITY_THRESHOLD: float = 0.5
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    HYBRID_TOP_K: int = 20

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # API
    API_PORT: int = 9005

    # LangSmith
    LANGCHAIN_TRACING_V2: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
