"""
RAG pipeline: combines retrieval (Milvus) + generation (LLM) for medical Q&A.
Handles the full flow: question -> embed -> search -> prompt -> answer.
"""

import logging
from typing import List, AsyncIterator
from langchain_core.messages import HumanMessage
from app.config import settings
from app.core import embedding, milvus_client, llm

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一个严谨的医疗AI助手。严格根据以下【已知医学背景知识】回答患者的【健康咨询问题】。
约束：1.回答必须完全基于背景知识，若背景知识未提及，必须回答："抱歉，基于目前资料无法解答，建议前往医院就诊。"
2.回复末尾强制加上："【免责声明】本建议由AI助手基于医学资料生成，仅供参考。"
3.回答要条理清晰，必要时使用编号或分点说明。"""

FALLBACK_ANSWER = "抱歉，基于目前资料无法解答，建议前往医院就诊。\n\n【免责声明】本建议由AI助手基于医学资料生成，仅供参考。"


def retrieve(query: str, top_k: int = None) -> List[dict]:
    """
    Retrieve top-K similar chunks from Milvus for the given query.
    Returns list of {doc_name, chunk_text, page_num, score}.
    """
    top_k = top_k or settings.TOP_K
    query_vector = embedding.encode_single(query)
    results = milvus_client.search(query_vector, top_k=top_k)
    return results


def build_prompt(question: str, chunks: List[dict]) -> str:
    """Build the RAG prompt with retrieved context and user question."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[来源{i}] 文档: {chunk['doc_name']}, 第{chunk['page_num']}页\n{chunk['chunk_text']}"
        )
    context = "\n\n".join(context_parts)

    return f"""{SYSTEM_PROMPT}

【已知医学背景知识】：
{context}

【健康咨询问题】：{question}"""


def generate_answer(question: str, top_k: int = None) -> dict:
    """
    Full RAG pipeline: retrieve -> check threshold -> generate.
    Returns {answer, sources, confidence}.
    """
    top_k = top_k or settings.TOP_K

    # Step 1: Retrieve
    chunks = retrieve(question, top_k)

    # Step 2: Check similarity threshold
    if not chunks or all(c["score"] < settings.SIMILARITY_THRESHOLD for c in chunks):
        logger.info(f"No relevant chunks found (threshold={settings.SIMILARITY_THRESHOLD}). Returning fallback.")
        return {
            "answer": FALLBACK_ANSWER,
            "sources": [],
            "confidence": max(c["score"] for c in chunks) if chunks else 0.0,
        }

    # Step 3: Build prompt and generate
    prompt = build_prompt(question, chunks)
    llm_client = llm.get_llm()

    try:
        response = llm_client.invoke([HumanMessage(content=prompt)])
        answer = response.content
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        answer = "抱歉，AI服务暂时不可用，请稍后再试。\n\n【免责声明】本建议由AI助手基于医学资料生成，仅供参考。"

    confidence = max(c["score"] for c in chunks)

    return {
        "answer": answer,
        "sources": chunks,
        "confidence": round(confidence, 4),
    }


async def generate_answer_stream(question: str, top_k: int = None) -> AsyncIterator[dict]:
    """
    Streaming RAG pipeline: retrieve -> check threshold -> stream generate.
    Yields: {"type": "sources", "data": ...}, {"type": "chunk", "data": ...}, {"type": "done"}
    """
    top_k = top_k or settings.TOP_K

    # Step 1: Retrieve
    chunks = retrieve(question, top_k)

    # Step 2: Check similarity threshold
    if not chunks or all(c["score"] < settings.SIMILARITY_THRESHOLD for c in chunks):
        confidence = max(c["score"] for c in chunks) if chunks else 0.0
        yield {"type": "sources", "data": {"sources": [], "confidence": round(confidence, 4)}}
        yield {"type": "chunk", "data": {"content": FALLBACK_ANSWER}}
        yield {"type": "done", "data": {}}
        return

    # Send sources first
    confidence = max(c["score"] for c in chunks)
    yield {"type": "sources", "data": {"sources": chunks, "confidence": round(confidence, 4)}}

    # Step 3: Stream generation
    prompt = build_prompt(question, chunks)
    llm_client = llm.get_llm_stream()

    try:
        async for chunk in llm_client.astream([HumanMessage(content=prompt)]):
            if chunk.content:
                yield {"type": "chunk", "data": {"content": chunk.content}}
    except Exception as e:
        logger.error(f"Streaming LLM failed: {e}")
        yield {"type": "chunk", "data": {"content": "\n\n抱歉，AI服务暂时不可用，请稍后再试。"}}

    yield {"type": "done", "data": {}}
