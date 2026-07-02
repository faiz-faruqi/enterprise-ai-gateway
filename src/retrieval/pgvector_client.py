"""
pgvector vector store client (Neon PostgreSQL backend).

Implements the same interface as VectorStore (Qdrant) so the
vector_store_factory can swap backends via VECTOR_STORE env var.

Schema (created automatically on first use):
    CREATE TABLE document_chunks (
        id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        chunk_id    TEXT NOT NULL,
        doc_name    TEXT NOT NULL,
        content     TEXT NOT NULL,
        chunk_index INTEGER NOT NULL,
        embedding   vector(384)
    );

Requires the pgvector extension to be enabled on the Neon database:
    CREATE EXTENSION IF NOT EXISTS vector;

Connection is read from DATABASE_URL env var (Neon connection string).
SSL mode is enforced for all Neon connections.
"""

import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
EMBEDDING_DIMENSION = 384  # Matches all-MiniLM-L6-v2


@dataclass
class ScoredChunk:
    """
    Lightweight substitute for qdrant_client.models.ScoredPoint.

    The query endpoint only reads .score and .payload, so this
    dataclass is a drop-in without importing qdrant-client.
    """

    score: float
    payload: dict[str, Any]


class PgVectorStore:
    """
    Async pgvector client backed by Neon PostgreSQL.

    All operations use a single asyncpg connection pool created at
    first use (lazy init) to avoid blocking application startup.
    """

    def __init__(self, database_url: str = DATABASE_URL) -> None:
        if not database_url:
            raise ValueError(
                "DATABASE_URL is required when VECTOR_STORE=pgvector. "
                "Set it to your Neon connection string."
            )
        self._dsn = database_url
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self._dsn,
                min_size=1,
                max_size=5,
                ssl="require",
            )
            logger.info("pgvector connection pool created.")
        return self._pool

    async def ensure_collection(self) -> None:
        """
        Ensure the pgvector extension and document_chunks table exist.

        Safe to call multiple times — uses CREATE IF NOT EXISTS guards.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    chunk_id    TEXT NOT NULL,
                    doc_name    TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    embedding   vector(384)
                );
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_chunks_embedding
                ON document_chunks
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100);
                """
            )
            logger.info("pgvector collection (document_chunks) ready.")

    async def upsert_chunks(
        self,
        chunks: list[dict[str, Any]],
        vectors: list[list[float]],
    ) -> int:
        """
        Index a batch of document chunks.

        Args:
            chunks: List of dicts with keys: document_name, content, chunk_index.
            vectors: Corresponding embedding vectors (list of 384-dim floats).

        Returns:
            Number of rows inserted.
        """
        await self.ensure_collection()
        pool = await self._get_pool()
        rows = [
            (
                str(uuid.uuid4()),
                chunk["document_name"],
                chunk["content"],
                chunk["chunk_index"],
                str(vector),  # asyncpg accepts vector as string representation
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        async with pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO document_chunks (chunk_id, doc_name, content, chunk_index, embedding)
                VALUES ($1, $2, $3, $4, $5::vector)
                """,
                rows,
            )
        logger.info("Upserted %d chunks into pgvector.", len(rows))
        return len(rows)

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[ScoredChunk]:
        """
        Return the top-k most semantically similar chunks using cosine distance.

        Returns a list of ScoredChunk objects compatible with the query endpoint.
        """
        pool = await self._get_pool()
        vector_str = str(query_vector)
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    chunk_id,
                    doc_name,
                    content,
                    chunk_index,
                    1 - (embedding <=> $1::vector) AS cosine_similarity
                FROM document_chunks
                ORDER BY embedding <=> $1::vector
                LIMIT $2
                """,
                vector_str,
                top_k,
            )
        return [
            ScoredChunk(
                score=float(row["cosine_similarity"]),
                payload={
                    "chunk_id": row["chunk_id"],
                    "document_name": row["doc_name"],
                    "content": row["content"],
                    "chunk_index": row["chunk_index"],
                },
            )
            for row in rows
        ]

    async def count(self) -> int:
        """Return the total number of indexed chunks."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM document_chunks;")
            return int(result)

    async def health_check(self) -> bool:
        """Return True if the pgvector database is reachable."""
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as exc:
            logger.warning("pgvector health check failed: %s", exc)
            return False
