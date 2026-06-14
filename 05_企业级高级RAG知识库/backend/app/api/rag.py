"""
RAG API routes: query and health check endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    RAGQueryRequest,
    RAGQueryResponse,
    SourceItem,
    HealthResponse,
    ServiceStatus,
)
from app.core import rag_pipeline
from app.core import bm25_search, milvus_client, reranker, vector_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(request: RAGQueryRequest):
    """
    RAG query endpoint.
    Flow: Hybrid Search -> Rerank -> Compress -> LLM Generate
    """
    try:
        result = rag_pipeline.generate_answer(
            question=request.question,
            top_k=request.top_k,
        )

        return RAGQueryResponse(
            answer=result["answer"],
            sources=[
                SourceItem(**s) for s in result["sources"]
            ],
            confidence=result["confidence"],
            tokens_used=result["tokens_used"],
            elapsed_ms=result["elapsed_ms"],
        )
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.
    Checks ES, Milvus, and Reranker service status.
    """
    services = []
    overall_status = "healthy"

    # Check Elasticsearch
    try:
        es = bm25_search.get_es_client()
        es_health = es.cluster.health()
        services.append(ServiceStatus(
            name="elasticsearch",
            status="ok",
            detail=f"cluster={es_health['status']}, indices={es_health['active_shards']} shards",
        ))
    except Exception as e:
        services.append(ServiceStatus(name="elasticsearch", status="error", detail=str(e)))
        overall_status = "unhealthy"

    # Check Milvus
    try:
        from pymilvus import utility
        version = utility.get_server_version()
        count = milvus_client.collection_count()
        services.append(ServiceStatus(
            name="milvus",
            status="ok",
            detail=f"version={version}, vectors={count}",
        ))
    except Exception as e:
        services.append(ServiceStatus(name="milvus", status="error", detail=str(e)))
        overall_status = "unhealthy"

    # Check Reranker
    reranker_status = reranker.check_reranker_health()
    services.append(ServiceStatus(
        name="reranker",
        **reranker_status,
    ))
    if reranker_status["status"] != "ok":
        overall_status = "degraded" if overall_status == "healthy" else overall_status

    # Check ES index count
    try:
        es_count = bm25_search.index_count()
        services.append(ServiceStatus(
            name="elasticsearch_index",
            status="ok",
            detail=f"{es_count} documents indexed",
        ))
    except Exception:
        pass

    return HealthResponse(status=overall_status, services=services)
