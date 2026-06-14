"""
BM25 Search via Elasticsearch with IK Chinese analyzer.
Provides keyword-based retrieval for hybrid search.
"""

import logging
from typing import List
from elasticsearch import Elasticsearch
from app.config import settings

logger = logging.getLogger(__name__)

_es_client: Elasticsearch | None = None
_index_created = False

# ES index mapping with IK analyzer
INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "doc_name": {"type": "keyword"},
            "chunk_text": {
                "type": "text",
                "analyzer": "ik_max_word",
                "search_analyzer": "ik_smart",
            },
            "page_num": {"type": "integer"},
            "chunk_id": {"type": "keyword"},
        }
    },
}


def get_es_client() -> Elasticsearch:
    """Get or initialize the Elasticsearch client (singleton)."""
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(
            hosts=[settings.ES_HOST],
            request_timeout=30,
            verify_certs=False,
            ssl_show_warn=False,
        )
        logger.info(f"Connected to Elasticsearch at {settings.ES_HOST}")
    return _es_client


def ensure_index() -> bool:
    """Create the ES index with IK analyzer if it doesn't exist."""
    global _index_created
    if _index_created:
        return True

    es = get_es_client()
    index_name = settings.ES_INDEX

    if es.indices.exists(index=index_name):
        logger.info(f"Index '{index_name}' already exists.")
        _index_created = True
        return True

    try:
        es.indices.create(index=index_name, body=INDEX_MAPPING)
        logger.info(f"Created index '{index_name}' with IK analyzer.")
        _index_created = True
        return True
    except Exception as e:
        logger.error(f"Failed to create index '{index_name}': {e}")
        return False


def index_chunks(chunks: List[dict]) -> int:
    """
    Bulk index chunks into Elasticsearch.
    Each chunk: {doc_name, chunk_text, page_num, chunk_id}
    """
    es = get_es_client()
    ensure_index()

    actions = []
    for i, chunk in enumerate(chunks):
        actions.append({"index": {"_index": settings.ES_INDEX}})
        actions.append({
            "doc_name": chunk["doc_name"],
            "chunk_text": chunk["chunk_text"],
            "page_num": chunk.get("page_num", 1),
            "chunk_id": chunk.get("chunk_id", str(i)),
        })

    if actions:
        resp = es.bulk(operations=actions, refresh=True)
        error_count = resp.get("errors", 0)
        if error_count:
            logger.warning(f"Bulk indexing had {error_count} errors.")
        logger.info(f"Indexed {len(chunks)} chunks into ES.")
    return len(chunks)


def bm25_search(query: str, top_k: int = None) -> List[dict]:
    """
    BM25 keyword search using Elasticsearch.
    Returns list of {doc_name, chunk_text, page_num, score}.
    """
    top_k = top_k or settings.HYBRID_TOP_K
    es = get_es_client()
    ensure_index()

    body = {
        "query": {
            "match": {
                "chunk_text": {
                    "query": query,
                    "analyzer": "ik_smart",
                }
            }
        },
        "size": top_k,
        "_source": ["doc_name", "chunk_text", "page_num"],
    }

    try:
        resp = es.search(index=settings.ES_INDEX, body=body)
    except Exception as e:
        logger.error(f"ES search failed: {e}")
        return []

    matches = []
    for hit in resp["hits"]["hits"]:
        matches.append({
            "doc_name": hit["_source"]["doc_name"],
            "chunk_text": hit["_source"]["chunk_text"],
            "page_num": hit["_source"].get("page_num", 1),
            "score": float(hit["_score"]),
        })

    return matches


def index_count() -> int:
    """Return total number of documents in the ES index."""
    es = get_es_client()
    ensure_index()
    resp = es.count(index=settings.ES_INDEX)
    return resp["count"]
