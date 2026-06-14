"""
Hybrid Search: combines BM25 (Elasticsearch) and Vector (Milvus) retrieval
using weighted Reciprocal Rank Fusion (RRF).
"""

import logging
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.bm25_search import bm25_search
from app.core.vector_search import vector_search
from app.config import settings

logger = logging.getLogger(__name__)


def _rank_fusion(
    result_lists: List[List[dict]],
    weights: List[float],
    k: int = 60,
) -> List[dict]:
    """
    Weighted Reciprocal Rank Fusion (RRF).
    score = sum( weight_i / (k + rank_i) )

    Args:
        result_lists: list of ranked result lists from different retrieval channels
        weights: weight for each channel
        k: RRF constant (default 60, standard value)
    """
    # Map chunk_text -> aggregated score + first occurrence metadata
    score_map: dict[str, dict] = {}

    for results, weight in zip(result_lists, weights):
        for rank, item in enumerate(results):
            key = item["chunk_text"]
            rrf_score = weight / (k + rank + 1)  # rank is 0-indexed

            if key not in score_map:
                score_map[key] = {
                    "doc_name": item["doc_name"],
                    "chunk_text": item["chunk_text"],
                    "page_num": item.get("page_num", 1),
                    "rrf_score": 0.0,
                    "bm25_score": 0.0,
                    "vector_score": 0.0,
                }

            score_map[key]["rrf_score"] += rrf_score

            # Track original scores for debugging
            if results is result_lists[0]:  # BM25
                score_map[key]["bm25_score"] = item.get("score", 0.0)
            else:  # Vector
                score_map[key]["vector_score"] = item.get("score", 0.0)

    # Sort by RRF score descending
    ranked = sorted(score_map.values(), key=lambda x: x["rrf_score"], reverse=True)
    return ranked


def hybrid_search(
    query: str,
    top_k: int = None,
    bm25_weight: float = None,
    vector_weight: float = None,
) -> List[dict]:
    """
    Dual-channel hybrid search with weighted RRF fusion.

    1. BM25 keyword search (Elasticsearch)
    2. Vector semantic search (Milvus)
    3. Merge, deduplicate, and fuse with weighted RRF

    Returns list of {doc_name, chunk_text, page_num, rrf_score, bm25_score, vector_score}.
    """
    top_k = top_k or settings.TOP_K
    bm25_weight = bm25_weight if bm25_weight is not None else settings.BM25_WEIGHT
    vector_weight = vector_weight if vector_weight is not None else settings.VECTOR_WEIGHT
    candidate_k = settings.HYBRID_TOP_K

    # Run both searches concurrently
    bm25_results = []
    vector_results = []

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(bm25_search, query, candidate_k): "bm25",
            executor.submit(vector_search, query, candidate_k): "vector",
        }
        for future in as_completed(futures):
            channel = futures[future]
            try:
                result = future.result()
                if channel == "bm25":
                    bm25_results = result
                else:
                    vector_results = result
            except Exception as e:
                logger.error(f"{channel} search failed: {e}")

    logger.info(
        f"Hybrid search: BM25 returned {len(bm25_results)}, "
        f"Vector returned {len(vector_results)}"
    )

    if not bm25_results and not vector_results:
        return []

    # Fuse with weighted RRF
    fused = _rank_fusion(
        [bm25_results, vector_results],
        [bm25_weight, vector_weight],
        k=settings.RRF_K,
    )

    # Return top_k after fusion
    return fused[:top_k]
