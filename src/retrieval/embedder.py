"""
Embedding wrapper using SentenceTransformers.

Model: all-MiniLM-L6-v2
  - 384-dimensional output
  - Optimized for semantic similarity
  - Runs locally — no external API dependency

The model is loaded once at startup and reused across requests.
Loading is deferred to first use (lazy) to avoid blocking app startup.
"""

import logging
import os
from functools import lru_cache
from typing import Union

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def _load_model(model_name: str) -> SentenceTransformer:
    """Load and cache the embedding model (singleton per process)."""
    logger.info("Loading embedding model: %s", model_name)
    return SentenceTransformer(model_name)


class Embedder:
    """
    Wraps SentenceTransformer to produce normalized float embeddings.

    Accepts a single string or a list of strings.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self._model_name = model_name

    @property
    def model(self) -> SentenceTransformer:
        return _load_model(self._model_name)

    def embed(self, texts: Union[str, list[str]]) -> list[list[float]]:
        """
        Produce embeddings for one or more text inputs.

        Returns:
            A list of float vectors, one per input text.
        """
        if isinstance(texts, str):
            texts = [texts]
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()

    def embed_single(self, text: str) -> list[float]:
        """Convenience method for embedding a single string."""
        return self.embed(text)[0]
