"""
Vector store factory.

Returns the appropriate VectorStore implementation based on the
VECTOR_STORE environment variable:

    VECTOR_STORE=qdrant    → QdrantVectorStore (default, used in local Docker Compose)
    VECTOR_STORE=pgvector  → PgVectorStore (used in Railway demo with Neon)

This allows the same codebase to serve both local development and the
cloud demo without any code changes — only environment variable differences.
"""

import logging
import os
from typing import Union

from src.retrieval.pgvector_client import PgVectorStore
from src.retrieval.qdrant_client import VectorStore as QdrantVectorStore

logger = logging.getLogger(__name__)

VECTOR_STORE_BACKEND = os.getenv("VECTOR_STORE", "qdrant").lower()

# Type alias for the shared interface
VectorStoreType = Union[QdrantVectorStore, PgVectorStore]


def get_vector_store() -> VectorStoreType:
    """
    Instantiate and return the configured vector store.

    Used as a FastAPI dependency:
        store: VectorStoreType = Depends(get_vector_store)

    The returned object always exposes:
        - ensure_collection() -> None
        - upsert_chunks(chunks, vectors) -> int
        - search(query_vector, top_k) -> list[ScoredPoint | ScoredChunk]
    """
    if VECTOR_STORE_BACKEND == "pgvector":
        logger.info("Vector store backend: pgvector (Neon)")
        return PgVectorStore()
    logger.info("Vector store backend: qdrant")
    return QdrantVectorStore()
