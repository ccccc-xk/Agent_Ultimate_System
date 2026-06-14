"""
Data import script: loads documents from data/ directory, splits them into chunks,
computes embeddings, and imports into Milvus.
Can be run independently: python -m app.core.data_import
"""

import os
import sys
import time
import logging

# Add parent to path for module imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config import settings
from app.loaders.document_loader import load_document
from app.splitter.text_splitter import split_documents
from app.core import embedding, milvus_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def import_documents(data_dir: str = None):
    """Import all PDF/MD documents from the data directory into Milvus."""
    data_dir = data_dir or DATA_DIR

    if not os.path.exists(data_dir):
        logger.error(f"Data directory not found: {data_dir}")
        return

    # Connect to Milvus and create collection
    logger.info("Connecting to Milvus...")
    milvus_client.connect()
    milvus_client.create_collection()

    # Pre-load embedding model
    logger.info("Loading embedding model...")
    embedding.get_model()

    # Find all supported files
    supported_ext = (".pdf", ".md", ".markdown")
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
        start_time = time.time()

        try:
            # Load document
            logger.info(f"Loading: {doc_name}")
            documents = load_document(file_path)

            # Split into chunks
            chunks = split_documents(documents)
            logger.info(f"  Split into {len(chunks)} chunks")

            if not chunks:
                logger.warning(f"  No chunks generated from {doc_name}, skipping.")
                continue

            # Compute embeddings
            texts = [c.page_content for c in chunks]
            page_nums = [c.metadata["page_num"] for c in chunks]
            embeddings = embedding.encode(texts)
            logger.info(f"  Computed {len(embeddings)} embeddings")

            # Insert into Milvus
            milvus_client.insert_chunks(
                doc_name=doc_name,
                chunks=texts,
                page_nums=page_nums,
                embeddings=embeddings,
            )

            elapsed = time.time() - start_time
            total_chunks += len(chunks)
            total_time += elapsed
            logger.info(f"  Done: {len(chunks)} chunks imported in {elapsed:.1f}s")

        except Exception as e:
            logger.error(f"  Failed to import {doc_name}: {e}")
            continue

    logger.info(f"\n=== Import Complete ===")
    logger.info(f"Total documents: {len(files)}")
    logger.info(f"Total chunks: {total_chunks}")
    logger.info(f"Total time: {total_time:.1f}s")


if __name__ == "__main__":
    import_documents()
