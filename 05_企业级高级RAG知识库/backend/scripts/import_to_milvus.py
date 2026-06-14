"""
Import documents into Milvus vector database.
Reads from data/ directory, splits, computes embeddings, and inserts.
"""

import os
import sys
import time
import logging

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.loaders.document_loader import load_document
from app.splitter.text_splitter import split_documents
from app.core import embedding, milvus_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def import_to_milvus(data_dir: str = None):
    """Import all supported documents into Milvus."""
    data_dir = data_dir or DATA_DIR

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return

    logger.info("Connecting to Milvus...")
    milvus_client.connect()
    milvus_client.create_collection()

    logger.info("Loading embedding model...")
    embedding.get_model()

    supported_ext = (".pdf", ".md", ".markdown", ".txt")
    files = [
        os.path.join(data_dir, f)
        for f in os.listdir(data_dir)
        if f.lower().endswith(supported_ext)
    ]

    if not files:
        logger.warning(f"No supported documents found in {data_dir}")
        return

    logger.info(f"Found {len(files)} document(s) to import.")
    total_chunks = 0
    total_time = 0

    for file_path in files:
        doc_name = os.path.basename(file_path)
        start = time.time()

        try:
            documents = load_document(file_path)
            chunks = split_documents(documents)
            logger.info(f"  {doc_name}: {len(chunks)} chunks")

            if not chunks:
                continue

            texts = [c.page_content for c in chunks]
            page_nums = [c.metadata.get("page_num", 1) for c in chunks]

            embeddings = embedding.encode(texts)
            logger.info(f"  {doc_name}: {len(embeddings)} embeddings computed")

            milvus_client.insert_chunks(
                doc_name=doc_name,
                chunks=texts,
                page_nums=page_nums,
                embeddings=embeddings,
            )

            elapsed = time.time() - start
            total_chunks += len(chunks)
            total_time += elapsed
            logger.info(f"  {doc_name}: imported in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"  Failed to import {doc_name}: {e}")

    logger.info(f"\n=== Milvus Import Complete ===")
    logger.info(f"Total documents: {len(files)}")
    logger.info(f"Total chunks: {total_chunks}")
    logger.info(f"Total time: {total_time:.1f}s")


if __name__ == "__main__":
    import_to_milvus()
