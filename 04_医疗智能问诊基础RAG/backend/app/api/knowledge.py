"""
Knowledge base management API: upload, list, delete documents.
"""

import os
import time
import logging
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import UploadResponse, KnowledgeItem, KnowledgeListResponse, DeleteResponse
from app.config import settings
from app.loaders.document_loader import load_document
from app.splitter.text_splitter import split_documents
from app.core import embedding, milvus_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF or Markdown document.
    Automatically: load -> split -> embed -> store in Milvus.
    """
    # Validate file type
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".pdf", ".md", ".markdown"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Only PDF and Markdown are supported."
        )

    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {size_mb:.1f}MB (max: {settings.MAX_FILE_SIZE_MB}MB)"
        )

    start_time = time.time()

    try:
        # Save to temp file
        suffix = ext
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        # Load document
        documents = load_document(tmp_path)
        if not documents:
            raise HTTPException(status_code=400, detail="No text content extracted from the document.")

        # Split into chunks
        chunks = split_documents(documents)
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks generated from the document.")

        # Remove existing data for same doc name (dedup)
        milvus_client.delete_by_doc(filename)

        # Compute embeddings
        texts = [c.page_content for c in chunks]
        page_nums = [c.metadata["page_num"] for c in chunks]
        embeddings = embedding.encode(texts)

        # Insert into Milvus
        milvus_client.insert_chunks(
            doc_name=filename,
            chunks=texts,
            page_nums=page_nums,
            embeddings=embeddings,
        )

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Uploaded '{filename}': {len(chunks)} chunks in {elapsed}s")

        return UploadResponse(
            doc_name=filename,
            chunk_count=len(chunks),
            elapsed_seconds=elapsed,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")
    finally:
        # Cleanup temp file
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/list", response_model=KnowledgeListResponse)
async def list_documents():
    """List all documents in the knowledge base with chunk counts."""
    try:
        docs = milvus_client.list_docs()
        return KnowledgeListResponse(
            documents=[KnowledgeItem(**d) for d in docs]
        )
    except Exception as e:
        logger.error(f"List failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/{doc_name}", response_model=DeleteResponse)
async def delete_document(doc_name: str):
    """Delete a document and all its chunks from the knowledge base."""
    try:
        deleted_count = milvus_client.delete_by_doc(doc_name)
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Document '{doc_name}' not found.")

        return DeleteResponse(
            deleted=True,
            doc_name=doc_name,
            deleted_chunks=deleted_count,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
