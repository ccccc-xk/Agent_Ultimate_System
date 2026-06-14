"""
Reranker: loads bge-reranker-large model locally for reranking candidates.
Filters out low-score results and returns top-N.
"""

import logging
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)

# Global model instance (lazy loading)
_reranker_tokenizer = None
_reranker_model = None


def _get_reranker():
    """Lazy-load the reranker model using transformers."""
    global _reranker_tokenizer, _reranker_model
    if _reranker_model is None:
        import os
        # Fix SSL issues for model loading
        os.environ.setdefault("PYTHONHTTPSVERIFY", "0")
        
        logger.info(f"Loading reranker model from: {settings.RERANKER_MODEL_PATH}")
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        
        _reranker_tokenizer = AutoTokenizer.from_pretrained(
            settings.RERANKER_MODEL_PATH, local_files_only=True
        )
        _reranker_model = AutoModelForSequenceClassification.from_pretrained(
            settings.RERANKER_MODEL_PATH, local_files_only=True
        )
        _reranker_model.eval()
        if torch.cuda.is_available():
            _reranker_model = _reranker_model.cuda()
            logger.info("Reranker model loaded on GPU.")
        else:
            logger.info("Reranker model loaded on CPU.")
    return _reranker_tokenizer, _reranker_model


def rerank(
    query: str,
    candidates: List[dict],
    top_n: int = None,
    threshold: float = None,
) -> List[dict]:
    """
    Rerank candidates using bge-reranker-large loaded locally.

    Args:
        query: user question
        candidates: list of {doc_name, chunk_text, page_num, ...}
        top_n: number of results to return (default: settings.TOP_K)
        threshold: minimum rerank score to keep (default: settings.RERANKER_THRESHOLD)

    Returns:
        List of candidates with rerank_score added, sorted by rerank_score desc.
        Only includes items with score >= threshold.
    """
    if not candidates:
        return []

    top_n = top_n or settings.TOP_K
    threshold = threshold if threshold is not None else settings.RERANKER_THRESHOLD

    documents = [c["chunk_text"] for c in candidates]

    try:
        import torch
        import torch.nn.functional as F
        tokenizer, model = _get_reranker()
        
        scores = []
        for doc in documents:
            inputs = tokenizer(
                query, doc,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
                # For cross-encoder reranker, use sigmoid on the logits
                score = torch.sigmoid(logits).item()
            scores.append(score)

    except Exception as e:
        logger.error(f"Reranker inference failed: {e}")
        # Fallback: return without reranking
        return [
            {**c, "rerank_score": c.get("score", 0.0), "rerank_rank": i + 1}
            for i, c in enumerate(candidates[:top_n])
        ]

    # Pair scores with candidates, filter by threshold
    reranked = []
    for i, score in enumerate(scores):
        if score < threshold:
            logger.debug(f"Filtered out (score={score:.4f} < {threshold}): {documents[i][:50]}...")
            continue
        original = candidates[i]
        reranked.append({
            **original,
            "rerank_score": float(score),
            "rerank_rank": i + 1,
        })

    # Sort by rerank_score descending, take top_n
    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    reranked = reranked[:top_n]

    logger.info(
        f"Reranked {len(candidates)} -> {len(reranked)} candidates "
        f"(threshold={threshold}, top_n={top_n})"
    )

    return reranked


def check_reranker_health() -> dict:
    """Check if the reranker model is loaded/available."""
    import os
    model_path = settings.RERANKER_MODEL_PATH
    config_file = os.path.join(model_path, "config.json")
    weights_file = os.path.join(model_path, "model.safetensors")

    if not os.path.exists(config_file):
        return {"status": "error", "detail": f"Reranker model not found at {model_path}"}
    if not os.path.exists(weights_file):
        return {"status": "error", "detail": f"Model weights missing at {model_path}"}

    try:
        _get_reranker()
        return {"status": "ok", "detail": "Reranker model loaded and ready."}
    except Exception as e:
        return {"status": "error", "detail": f"Failed to load reranker: {e}"}
