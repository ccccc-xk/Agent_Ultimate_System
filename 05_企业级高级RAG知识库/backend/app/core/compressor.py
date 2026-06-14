"""
Context Compressor: cleans, deduplicates, and compresses retrieved context
before sending to the LLM. Targets >40% token reduction.
"""

import re
import logging
from typing import List, Tuple
from app.models.schemas import CompressionReport

logger = logging.getLogger(__name__)

# Try tiktoken for accurate token counting
try:
    import tiktoken
    _encoder = tiktoken.get_encoding("cl100k_base")
    _has_tiktoken = True
except ImportError:
    _has_tiktoken = False
    logger.warning("tiktoken not installed; using character-based token estimation.")


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken or fallback to character estimation."""
    if _has_tiktoken:
        return len(_encoder.encode(text))
    # Rough estimate: 1 token ~= 1.5 chars for Chinese
    return int(len(text) / 1.5)


def _clean_html(text: str) -> str:
    """Remove HTML tags."""
    return re.sub(r'<[^>]+>', '', text)


def _clean_whitespace(text: str) -> str:
    """Collapse multiple whitespace, newlines, tabs into single spaces."""
    text = re.sub(r'[\t\r]+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def _deduplicate_sentences(text: str, jaccard_threshold: float = 0.85) -> str:
    """
    Remove near-duplicate sentences using Jaccard similarity.
    Preserves the first occurrence.
    """
    # Split on Chinese sentence endings + period + exclamation + question mark
    sentences = re.split(r'(?<=[。！？.!?])', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= 1:
        return text

    def jaccard(s1: str, s2: str) -> float:
        set1 = set(s1)
        set2 = set(s2)
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0.0

    kept = []
    for sent in sentences:
        is_dup = False
        for kept_sent in kept:
            if jaccard(sent, kept_sent) > jaccard_threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(sent)

    return ''.join(kept)


def _remove_redundant_patterns(text: str) -> str:
    """
    Remove common redundant patterns in Chinese medical documents:
    - Repeated disclaimer/attribution lines
    - Boilerplate phrases
    """
    # Remove repeated attribution lines
    text = re.sub(r'(【免责声明】.*?仅供参考[。]?)', '', text)
    # Remove empty brackets
    text = re.sub(r'【[^】]{0,2}】', '', text)
    # Remove markdown artifacts
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    return text


def compress_context(chunks: List[dict]) -> Tuple[str, CompressionReport]:
    """
    Compress retrieved context chunks.

    Args:
        chunks: list of {chunk_text, doc_name, ...}

    Returns:
        (compressed_text, CompressionReport)
    """
    steps = []

    # Combine all chunk texts
    raw_text = '\n\n'.join([c['chunk_text'] for c in chunks])
    original_tokens = count_tokens(raw_text)
    steps.append(f"Original: {len(chunks)} chunks, {original_tokens} tokens")

    # Step 1: Clean HTML
    text = _clean_html(raw_text)
    tokens_after = count_tokens(text)
    steps.append(f"HTML removal: {original_tokens} -> {tokens_after} tokens")

    # Step 2: Clean whitespace
    text = _clean_whitespace(text)
    tokens_after_ws = count_tokens(text)
    steps.append(f"Whitespace cleanup: {tokens_after} -> {tokens_after_ws} tokens")

    # Step 3: Remove redundant patterns
    text = _remove_redundant_patterns(text)
    tokens_after_rr = count_tokens(text)
    steps.append(f"Redundancy removal: {tokens_after_ws} -> {tokens_after_rr} tokens")

    # Step 4: Deduplicate sentences
    text = _deduplicate_sentences(text)
    compressed_tokens = count_tokens(text)
    steps.append(f"Sentence dedup: {tokens_after_rr} -> {compressed_tokens} tokens")

    # Calculate compression ratio
    compression_ratio = 1.0 - (compressed_tokens / original_tokens) if original_tokens > 0 else 0.0

    report = CompressionReport(
        original_tokens=original_tokens,
        compressed_tokens=compressed_tokens,
        compression_ratio=round(compression_ratio, 4),
        steps=steps,
    )

    logger.info(
        f"Compression: {original_tokens} -> {compressed_tokens} tokens "
        f"(ratio={compression_ratio:.1%})"
    )

    return text, report
