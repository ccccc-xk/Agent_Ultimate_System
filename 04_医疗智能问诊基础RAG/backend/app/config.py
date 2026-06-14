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
    MILVUS_COLLECTION: str = "medical_knowledge"

    # Embedding Configuration
    EMBEDDING_MODEL_PATH: str = "BAAI/bge-large-zh-v1.5"
    EMBEDDING_DIMENSION: int = 1024

    # RAG Configuration
    TOP_K: int = 3
    SIMILARITY_THRESHOLD: float = 0.5
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:8082,http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
