"""
Document loader: supports PDF and Markdown files.
Adapted from project 04.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Simple document representation."""
    page_content: str
    metadata: dict = field(default_factory=dict)


def load_document(file_path: str) -> List[Document]:
    """Load a document from file path. Supports .pdf, .md, .markdown, .txt."""
    ext = os.path.splitext(file_path)[1].lower()
    doc_name = os.path.basename(file_path)

    if ext == ".pdf":
        return _load_pdf(file_path, doc_name)
    elif ext in (".md", ".markdown", ".txt"):
        return _load_text(file_path, doc_name)
    else:
        logger.warning(f"Unsupported file format: {ext}")
        return []


def _load_pdf(file_path: str, doc_name: str) -> List[Document]:
    """Load PDF using PyMuPDF."""
    import fitz
    docs = []
    pdf = fitz.open(file_path)
    for page_num, page in enumerate(pdf, 1):
        text = page.get_text()
        if text.strip():
            docs.append(Document(
                page_content=text,
                metadata={"doc_name": doc_name, "page_num": page_num},
            ))
    pdf.close()
    logger.info(f"Loaded PDF '{doc_name}': {len(docs)} pages")
    return docs


def _load_text(file_path: str, doc_name: str) -> List[Document]:
    """Load text/markdown file."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    logger.info(f"Loaded text '{doc_name}': {len(text)} chars")
    return [Document(
        page_content=text,
        metadata={"doc_name": doc_name, "page_num": 1},
    )]
