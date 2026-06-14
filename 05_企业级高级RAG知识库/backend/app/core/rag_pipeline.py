"""
RAG Pipeline: complete retrieval-augmented generation chain.
Hybrid Search -> Rerank -> Compress -> LLM Generate

LangSmith tracing is enabled via environment variables (LANGCHAIN_TRACING_V2=true),
so all LangChain calls are automatically traced.
"""

import logging
import time
from typing import List
from langchain_core.messages import HumanMessage
from app.core import (
    hybrid_search,
    reranker,
    compressor,
    llm,
)
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个严谨的企业级AI助手。严格根据以下【已知背景知识】回答用户的【问题】。

约束：
1. 回答必须完全基于背景知识，若背景知识未涉及，必须回答："抱歉，基于目前资料无法解答，建议咨询相关专业人士。"
2. 回答要条理清晰，必要时使用编号或分点说明。
3. 引用信息时注明来源文档名称。
"""

FALLBACK_ANSWER = "抱歉，基于目前资料无法解答，建议咨询相关专业人士。"


def build_prompt(question: str, context: str) -> str:
    """Build the RAG prompt with compressed context and user question."""
    return f"""{SYSTEM_PROMPT}

【已知背景知识】：
{context}

【问题】：{question}"""


def generate_answer(question: str, top_k: int = None) -> dict:
    """
    Full RAG pipeline:
    1. Hybrid search (BM25 + Vector with RRF)
    2. Rerank with bge-reranker-large
    3. Compress context (token optimization)
    4. LLM generate answer

    Returns: {answer, sources, confidence, tokens_used, compression_report}
    """
    start_time = time.time()
    top_k = top_k or settings.TOP_K

    # Step 1: Hybrid Search
    logger.info(f"[Pipeline] Hybrid search for: {question}")
    candidates = hybrid_search.hybrid_search(question)

    if not candidates:
        logger.info("[Pipeline] No candidates found.")
        return {
            "answer": FALLBACK_ANSWER,
            "sources": [],
            "confidence": 0.0,
            "tokens_used": 0,
            "elapsed_ms": int((time.time() - start_time) * 1000),
        }

    # Step 2: Rerank
    logger.info(f"[Pipeline] Reranking {len(candidates)} candidates...")
    reranked = reranker.rerank(question, candidates, top_n=top_k)

    if not reranked:
        logger.info("[Pipeline] No candidates survived reranking threshold.")
        return {
            "answer": FALLBACK_ANSWER,
            "sources": [],
            "confidence": 0.0,
            "tokens_used": 0,
            "elapsed_ms": int((time.time() - start_time) * 1000),
        }

    # Step 3: Compress Context
    logger.info(f"[Pipeline] Compressing context from {len(reranked)} chunks...")
    compressed_text, comp_report = compressor.compress_context(reranked)
    logger.info(
        f"[Pipeline] Compression: {comp_report.original_tokens} -> "
        f"{comp_report.compressed_tokens} tokens ({comp_report.compression_ratio:.1%})"
    )

    # Step 4: LLM Generate
    logger.info("[Pipeline] Generating answer with LLM...")
    prompt = build_prompt(question, compressed_text)

    try:
        llm_client = llm.get_llm()
        response = llm_client.invoke([HumanMessage(content=prompt)])
        answer = response.content

        # Estimate tokens used (prompt + response)
        prompt_tokens = compressor.count_tokens(prompt)
        response_tokens = compressor.count_tokens(answer)
        tokens_used = prompt_tokens + response_tokens
    except Exception as e:
        logger.error(f"[Pipeline] LLM invocation failed: {e}")
        answer = "抱歉，AI服务暂时不可用，请稍后再试。"
        tokens_used = 0

    # Build response
    confidence = max(c.get("rerank_score", c.get("rrf_score", 0.0)) for c in reranked)
    sources = [
        {
            "doc_name": c["doc_name"],
            "chunk_text": c["chunk_text"][:200] + "..." if len(c["chunk_text"]) > 200 else c["chunk_text"],
            "score": round(c.get("rerank_score", c.get("rrf_score", 0.0)), 4),
        }
        for c in reranked
    ]

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(f"[Pipeline] Done in {elapsed_ms}ms, {tokens_used} tokens")

    return {
        "answer": answer,
        "sources": sources,
        "confidence": round(confidence, 4),
        "tokens_used": tokens_used,
        "elapsed_ms": elapsed_ms,
    }
