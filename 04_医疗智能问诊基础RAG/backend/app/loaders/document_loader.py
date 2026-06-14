"""
Document loader: supports PDF and Markdown file formats.
Extracts text content with metadata (doc_name, page_num).
"""

import os
import fitz  # PyMuPDF
from typing import List
from dataclasses import dataclass


@dataclass
class Document:
    """Represents a loaded document page/section."""
    page_content: str
    metadata: dict


def load_pdf(file_path: str) -> List[Document]:
    """Load a PDF file and extract text per page."""
    doc_name = os.path.basename(file_path)
    documents = []

    pdf = fitz.open(file_path)
    for page_num in range(len(pdf)):
        page = pdf[page_num]
        text = page.get_text("text").strip()
        if text:
            documents.append(Document(
                page_content=text,
                metadata={"doc_name": doc_name, "page_num": page_num + 1}
            ))
    pdf.close()
    return documents


def load_markdown(file_path: str) -> List[Document]:
    """Load a Markdown file."""
    doc_name = os.path.basename(file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    if not text:
        return []

    return [Document(
        page_content=text,
        metadata={"doc_name": doc_name, "page_num": 1}
    )]


def load_document(file_path: str) -> List[Document]:
    """Auto-detect file format and load document."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext in (".md", ".markdown"):
        return load_markdown(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only PDF and Markdown are supported.")
