"""
LLM client: wraps OpenAI-compatible API (Qwen via DashScope) for chat and streaming.
Uses LangChain ChatOpenAI for unified interface.
"""

import logging
from langchain_openai import ChatOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

_llm = None
_llm_stream = None


def get_llm() -> ChatOpenAI:
    """Get or initialize the LLM client (singleton)."""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
            temperature=0.1,
            max_tokens=2048,
        )
        logger.info(f"LLM initialized: {settings.LLM_MODEL_NAME}")
    return _llm


def get_llm_stream() -> ChatOpenAI:
    """Get or initialize the streaming LLM client (singleton)."""
    global _llm_stream
    if _llm_stream is None:
        _llm_stream = ChatOpenAI(
            model=settings.LLM_MODEL_NAME,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL,
            temperature=0.1,
            max_tokens=2048,
            streaming=True,
        )
        logger.info(f"Streaming LLM initialized: {settings.LLM_MODEL_NAME}")
    return _llm_stream
