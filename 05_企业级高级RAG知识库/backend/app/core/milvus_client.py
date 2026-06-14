"""
Milvus client: handles connection, collection management, and CRUD operations
for the enterprise knowledge vector database.
Adapted from project 04 with enterprise_knowledge collection.
"""

import logging
from datetime import datetime
from typing import List, Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = settings.MILVUS_COLLECTION


def connect():
    """Establish connection to Milvus server."""
    try:
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
        )
        logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        raise


def create_collection() -> Collection:
    """Create the enterprise_knowledge collection with schema and index."""
    if utility.has_collection(COLLECTION_NAME):
        logger.info(f"Collection '{COLLECTION_NAME}' already exists.")
        collection = Collection(COLLECTION_NAME)
        collection.load()
        return collection

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="page_num", dtype=DataType.INT32),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
        FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=32),
    ]

    schema = CollectionSchema(
        fields=fields,
        description="Enterprise knowledge base for advanced RAG",
        enable_dynamic_field=False,
    )

    collection = Collection(name=COLLECTION_NAME, schema=schema)

    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    logger.info(f"Created collection '{COLLECTION_NAME}' with IVF_FLAT index.")

    collection.load()
    return collection


def get_collection() -> Collection:
    """Get the existing collection."""
    return Collection(COLLECTION_NAME)


def insert_chunks(
    doc_name: str,
    chunks: List[str],
    page_nums: List[int],
    embeddings: List[List[float]],
) -> int:
    """Insert document chunks with embeddings into Milvus."""
    collection = get_collection()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = [
        [doc_name] * len(chunks),
        chunks,
        page_nums,
        embeddings,
        [now] * len(chunks),
    ]

    collection.insert(data)
    collection.flush()
    logger.info(f"Inserted {len(chunks)} chunks for doc '{doc_name}'.")
    return len(chunks)


def search(query_embedding: List[float], top_k: int = None) -> List[dict]:
    """Search for similar chunks using cosine similarity."""
    top_k = top_k or settings.HYBRID_TOP_K
    collection = get_collection()

    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 16},
    }

    results = collection.search(
        data=[query_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        output_fields=["doc_name", "chunk_text", "page_num"],
    )

    matches = []
    for hit in results[0]:
        matches.append({
            "doc_name": hit.entity.get("doc_name"),
            "chunk_text": hit.entity.get("chunk_text"),
            "page_num": hit.entity.get("page_num"),
            "score": float(hit.score),
        })

    return matches


def delete_by_doc(doc_name: str) -> int:
    """Delete all chunks belonging to a specific document."""
    collection = get_collection()
    expr = f'doc_name == "{doc_name}"'
    results = collection.query(expr=expr, output_fields=["id"])
    count = len(results)
    if count > 0:
        collection.delete(expr)
        collection.flush()
        logger.info(f"Deleted {count} chunks for doc '{doc_name}'.")
    return count


def collection_count() -> int:
    """Return total number of entities in the collection."""
    collection = get_collection()
    return collection.num_entities
