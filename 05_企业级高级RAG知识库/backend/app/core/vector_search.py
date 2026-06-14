"""
Vector Search via Milvus.
Wraps milvus_client for use in hybrid search.
"""

import logging
from typing import List
from app.core import milvus_client, embedding
from app.config import settings

logger = logging.getLogger(__name__)

_initialized = False


def ensure_initialized():
    """Ensure Milvus connection and collection are ready."""
    global _initialized
    if not _initialized:
        milvus_client.connect()
        milvus_client.create_collection()
        _initialized = True


def vector_search(query: str, top_k: int = None) -> List[dict]:
    """
    Semantic search via Milvus.
    Returns list of {doc_name, chunk_text, page_num, score}.
    """
    top_k = top_k or settings.HYBRID_TOP_K
    ensure_initialized()

    query_vector = embedding.encode_single(query)
    results = milvus_client.search(query_vector, top_k=top_k)

    return results
