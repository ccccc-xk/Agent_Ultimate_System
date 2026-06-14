"""
Embedding module: loads BGE-large-zh model and computes text embeddings.
Singleton pattern - model is loaded once at application startup.
"""

import logging
import os
from typing import List
from app.config import settings

logger = logging.getLogger(__name__)

# Ensure all HuggingFace caches are on D drive, not C drive
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_cache_root = os.path.join(_project_root, '.cache')

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HOME'] = os.path.join(_cache_root, 'huggingface')
os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(_cache_root, 'sentence_transformers')
os.environ['TORCH_HOME'] = os.path.join(_cache_root, 'torch')
os.environ['HF_HUB_DISABLE_XET'] = '1'  # Avoid CDN connection issues

# Global singleton
_model = None
_model_loaded = False


def get_model():
    """Get or initialize the embedding model (singleton)."""
    global _model, _model_loaded
    if _model is None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_PATH} ...")
        logger.info(f"Model cache dir: {os.environ.get('SENTENCE_TRANSFORMERS_HOME')}")
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_PATH)
        _model_loaded = True
        logger.info(f"Embedding model loaded successfully. Dimension: {_model.get_sentence_embedding_dimension()}")
    return _model


def encode(texts: List[str]) -> List[List[float]]:
    """
    Compute embeddings for a list of texts.
    Returns list of 1024-dimensional float vectors.
    """
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def encode_single(text: str) -> List[float]:
    """Compute embedding for a single text."""
    return encode([text])[0]


def is_loaded() -> bool:
    """Check if the model has been loaded."""
    return _model_loaded
