"""
Import documents into Elasticsearch with IK analyzer.
Reads from data/ directory, splits into chunks, and bulk indexes.
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
from app.core import bm25_search

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def import_to_es(data_dir: str = None):
    """Import all supported documents into Elasticsearch."""
    data_dir = data_dir or DATA_DIR

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return

    # Ensure ES index exists
    logger.info("Connecting to Elasticsearch...")
    bm25_search.ensure_index()

    # Find all supported files
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

    for file_path in files:
        doc_name = os.path.basename(file_path)
        start = time.time()

        try:
            documents = load_document(file_path)
            chunks = split_documents(documents)
            logger.info(f"  {doc_name}: {len(chunks)} chunks")

            if not chunks:
                continue

            es_chunks = [
                {
                    "doc_name": doc_name,
                    "chunk_text": c.page_content,
                    "page_num": c.metadata.get("page_num", 1),
                    "chunk_id": f"{doc_name}_{i}",
                }
                for i, c in enumerate(chunks)
            ]

            bm25_search.index_chunks(es_chunks)
            elapsed = time.time() - start
            total_chunks += len(chunks)
            logger.info(f"  {doc_name}: indexed in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"  Failed to import {doc_name}: {e}")

    logger.info(f"\n=== ES Import Complete ===")
    logger.info(f"Total documents: {len(files)}")
    logger.info(f"Total chunks: {total_chunks}")


if __name__ == "__main__":
    import_to_es()
