"""
Qdrant vector store client.

Handles document chunk storage and semantic retrieval.
Embedding is handled upstream by the Embedder class;
this client operates on pre-computed vectors.
"""

import logging
import os
import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

logger = logging.getLogger(__name__)

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "enterprise-docs")
EMBEDDING_DIMENSION = 384  # Matches all-MiniLM-L6-v2 output dimension


class VectorStore:
    """
    Async Qdrant client for document chunk operations.

    Collection schema:
        vector: float[384]   — sentence embedding
        payload: {
            document_name: str,
            chunk_id: str,
            content: str,
            chunk_index: int
        }
    """

    def __init__(
        self,
        host: str = QDRANT_HOST,
        port: int = QDRANT_PORT,
        collection: str = QDRANT_COLLECTION,
    ) -> None:
        self._client = AsyncQdrantClient(host=host, port=port)
        self._collection = collection

    async def ensure_collection(self) -> None:
        """Create the collection if it does not already exist."""
        collections = await self._client.get_collections()
        names = [c.name for c in collections.collections]
        if self._collection not in names:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Created collection: %s", self._collection)

    async def upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
        vectors: list[list[float]],
    ) -> int:
        """
        Index a batch of document chunks.

        Args:
            chunks: List of dicts with keys: document_name, content, chunk_index.
            vectors: Corresponding embedding vectors.

        Returns:
            Number of points upserted.
        """
        await self.ensure_collection()
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "document_name": chunk["document_name"],
                    "chunk_id": str(uuid.uuid4()),
                    "content": chunk["content"],
                    "chunk_index": chunk["chunk_index"],
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        await self._client.upsert(
            collection_name=self._collection,
            points=points,
        )
        return len(points)

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[ScoredPoint]:
        """Return the top-k most semantically similar chunks."""
        return await self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True,
        )
