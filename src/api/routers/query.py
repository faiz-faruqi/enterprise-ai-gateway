"""
Query endpoint.

This is the core of the platform — the endpoint that:
  1. Embeds the user query
  2. Retrieves relevant document chunks from Qdrant
  3. Assembles a grounded prompt
  4. Checks the Redis cache
  5. Routes to Ollama (primary) or OpenRouter (fallback)
  6. Writes the response to cache
  7. Returns the answer with source attribution

Each step maps to a distinct architectural component, keeping
the orchestration logic readable and each component independently testable.
"""

import logging
import time

from fastapi import APIRouter, HTTPException

from src.cache.redis_cache import ResponseCache
from src.inference.ollama_client import OllamaClient
from src.inference.openrouter_client import OpenRouterClient
from src.inference.router import InferenceRouter, ProviderResult
from src.models.schemas import (
    InferenceProvider,
    QueryRequest,
    QueryResponse,
    SourceDocument,
)
from src.retrieval.embedder import Embedder
from src.retrieval.qdrant_client import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter()

# Component instantiation — in production, use FastAPI's Depends()
# for full dependency injection with lifecycle management.
_embedder = Embedder()
_vector_store = VectorStore()
_cache = ResponseCache()
_inference_router = InferenceRouter(
    ollama=OllamaClient(),
    openrouter=OpenRouterClient(),
)

PROMPT_TEMPLATE = """You are an enterprise document assistant. Answer the user's question
using ONLY the information in the provided context. If the answer is not present in the
context, say so clearly. Do not speculate or use outside knowledge.

Context:
{context}

Question: {question}

Answer:"""


@router.post("/", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Process a natural language query over indexed enterprise documents.

    Steps:
      1. Embed the query
      2. Retrieve top-k chunks from Qdrant
      3. Build a grounded prompt
      4. Check Redis cache
      5. Run inference (local → cloud fallback)
      6. Cache and return response
    """
    start = time.perf_counter()

    # ── Step 1: Embed ────────────────────────────────────────────
    query_vector = _embedder.embed_single(request.query)

    # ── Step 2: Retrieve ─────────────────────────────────────────
    hits = await _vector_store.search(query_vector, top_k=request.top_k)
    if not hits:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found. Ensure documents have been ingested.",
        )

    sources = [
        SourceDocument(
            chunk_id=hit.payload["chunk_id"],
            document_name=hit.payload["document_name"],
            content_preview=hit.payload["content"][:300],
            relevance_score=round(hit.score, 4),
        )
        for hit in hits
    ]

    # ── Step 3: Build grounded prompt ────────────────────────────
    context_blocks = "\n\n".join(
        f"[{hit.payload['document_name']}]\n{hit.payload['content']}"
        for hit in hits
    )
    grounded_prompt = PROMPT_TEMPLATE.format(
        context=context_blocks,
        question=request.query,
    )

    # ── Step 4: Cache lookup ─────────────────────────────────────
    cached_answer = await _cache.get(grounded_prompt)
    if cached_answer:
        latency = (time.perf_counter() - start) * 1000
        return QueryResponse(
            answer=cached_answer,
            provider=InferenceProvider.cache,
            cached=True,
            sources=sources,
            latency_ms=round(latency, 2),
        )

    # ── Step 5: Inference ────────────────────────────────────────
    answer, used_provider = await _inference_router.complete(
        prompt=grounded_prompt,
        force_cloud=request.force_cloud,
    )

    provider_enum = (
        InferenceProvider.local
        if used_provider == ProviderResult.LOCAL
        else InferenceProvider.cloud
    )

    # ── Step 6: Cache write ──────────────────────────────────────
    await _cache.set(grounded_prompt, answer)

    latency = (time.perf_counter() - start) * 1000
    return QueryResponse(
        answer=answer,
        provider=provider_enum,
        cached=False,
        sources=sources,
        latency_ms=round(latency, 2),
    )
