"""
Text splitter: splits documents into chunks with overlap.
Optimized for Chinese text with Chinese-aware separators.
Adapted from project 04.
"""

from typing import List
from app.loaders.document_loader import Document
from app.config import settings


def split_text(text: str, chunk_size: int = None, chunk_overlap: int = None) -> List[str]:
    """
    Split text into chunks with overlap.
    Uses a hierarchy of separators optimized for Chinese text.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text]

    separators = ["\n\n", "\n", "\u3002", "\uff1b", "\uff01", "\uff1f", ".", "\uff0c", ",", " "]
    return _recursive_split(text, separators, chunk_size, chunk_overlap)


def _recursive_split(
    text: str,
    separators: List[str],
    chunk_size: int,
    chunk_overlap: int,
) -> List[str]:
    """Recursively split text using separator hierarchy."""
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    separator = ""
    for sep in separators:
        if sep in text:
            separator = sep
            break

    if not separator:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start += chunk_size - chunk_overlap
        return chunks

    splits = text.split(separator)
    chunks = []
    current = ""

    for part in splits:
        candidate = current + separator + part if current else part

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())

            if len(part) > chunk_size:
                sub_chunks = _recursive_split(
                    part, separators[1:] if separators else [], chunk_size, chunk_overlap
                )
                chunks.extend(sub_chunks)
                current = ""
            else:
                if chunks and chunk_overlap > 0:
                    last_chunk = chunks[-1]
                    overlap_text = last_chunk[-chunk_overlap:] if len(last_chunk) > chunk_overlap else last_chunk
                    current = overlap_text + separator + part
                    if len(current) > chunk_size:
                        current = part
                else:
                    current = part

    if current.strip():
        chunks.append(current.strip())

    return chunks


def split_documents(documents: List[Document], chunk_size: int = None, chunk_overlap: int = None) -> List[Document]:
    """Split a list of documents into chunks, preserving metadata."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    result = []
    for doc in documents:
        chunks = split_text(doc.page_content, chunk_size, chunk_overlap)
        for chunk_text in chunks:
            if chunk_text:
                result.append(Document(
                    page_content=chunk_text,
                    metadata=doc.metadata.copy(),
                ))
    return result
