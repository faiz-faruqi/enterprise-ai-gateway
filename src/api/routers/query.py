"""
Query endpoint.

This is the core of the platform — the endpoint that:
  1. Classifies the user query to produce a QueryProfile
  2. Conditionally embeds and retrieves documents (RAG) if rag_needed=True
  3. Assembles a grounded (RAG) or direct prompt
  4. Checks the Redis cache
  5. Routes to the optimal inference model via the Decision Engine
  6. Writes the response to cache
  7. Returns the answer with source attribution and routing metadata

RAG is bypassed entirely when the classifier determines the query is a
general knowledge question (rag_needed=False), saving embedding compute
and vector-store round-trips for those requests.

Each step maps to a distinct architectural component, keeping the
orchestration logic readable and each component independently testable.
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import (
    get_cache,
    get_classifier,
    get_decision_engine,
    get_embedder,
    get_inference_router,
    get_vector_store_dep,
)
from src.cache.redis_cache import ResponseCache
from src.inference.router import InferenceRouter, ProviderResult
from src.models.schemas import (
    InferenceProvider,
    QueryRequest,
    QueryResponse,
    SourceDocument,
)
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store_factory import VectorStoreType
from src.routing.classifier import QueryClassifier
from src.routing.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)

router = APIRouter()

# Used when RAG retrieval has run — grounds the answer in document context.
GROUNDED_PROMPT_TEMPLATE = """You are an enterprise document assistant. Answer the user's question \
using ONLY the information in the provided context. If the answer is not present in the \
context, say so clearly. Do not speculate or use outside knowledge.

Context:
{context}

Question: {question}

Answer:"""

# Used when RAG is skipped — the model answers from its own knowledge.
DIRECT_PROMPT_TEMPLATE = """You are a helpful enterprise AI assistant. \
Answer the following question clearly and concisely.

Question: {question}

Answer:"""


@router.post("/", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    embedder: Embedder = Depends(get_embedder),
    store: VectorStoreType = Depends(get_vector_store_dep),
    cache: ResponseCache = Depends(get_cache),
    inference_router: InferenceRouter = Depends(get_inference_router),
    classifier: QueryClassifier = Depends(get_classifier),
    decision_engine: DecisionEngine = Depends(get_decision_engine),
) -> QueryResponse:
    """
    Process a natural language query over indexed enterprise documents.

    Steps:
      1. Classify the query (Phase 2) — produces rag_needed flag
      2. If rag_needed: embed → retrieve → build grounded prompt
         If not rag_needed: build a direct prompt, skip vector store
      3. Check Redis cache
      4. Run inference via Decision Engine (Phase 3)
      5. Cache and return response with source attribution
    """
    start = time.perf_counter()

    # ── Step 0: Classify the query (Phase 2) ──────────────────────
    # Produce a multi-dimensional QueryProfile before any retrieval or
    # inference. The Decision Engine (Phase 3) and rag_needed flag both
    # consume this profile.
    profile = classifier.classify(request.query)

    sources: list[SourceDocument] = []

    if profile.rag_needed:
        # ── Step 1: Embed ────────────────────────────────────────────
        query_vector = embedder.embed_single(request.query)

        # ── Step 2: Retrieve ─────────────────────────────────────────
        hits = await store.search(query_vector, top_k=request.top_k)
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

        # ── Step 3a: Build grounded prompt (RAG) ─────────────────────
        context_blocks = "\n\n".join(
            f"[{hit.payload['document_name']}]\n{hit.payload['content']}"
            for hit in hits
        )
        prompt = GROUNDED_PROMPT_TEMPLATE.format(
            context=context_blocks,
            question=request.query,
        )
        logger.info("RAG pipeline active: %d chunks retrieved.", len(hits))
    else:
        # ── Step 3b: Build direct prompt (no RAG) ────────────────────
        # Skip embedding and vector retrieval — saves compute and DB cost.
        prompt = DIRECT_PROMPT_TEMPLATE.format(question=request.query)
        logger.info("RAG bypassed: classifier flagged query as general knowledge.")

    # ── Step 4: Cache lookup ─────────────────────────────────────
    cached_answer = await cache.get(prompt)
    if cached_answer:
        latency = (time.perf_counter() - start) * 1000
        return QueryResponse(
            answer=cached_answer,
            provider=InferenceProvider.cache,
            cached=True,
            sources=sources,
            latency_ms=round(latency, 2),
            classification=profile,
        )

    # ── Step 5: Inference ────────────────────────────────────────
    # Phase 3: automatic model selection via the Decision Engine.
    #   - If the caller specified an explicit model (request.model),
    #     use it directly (Phase 1 explicit selection).
    #   - If force_cloud is set, use the legacy cloud path.
    #   - Otherwise, let the Decision Engine select the optimal model
    #     based on the QueryProfile and cost budget.
    routing_decision = None

    if request.model:
        answer, used_provider, model_alias = await inference_router.complete_with_model(
            prompt=prompt,
            model_alias=request.model,
        )
    elif request.force_cloud:
        answer, used_provider = await inference_router.complete(
            prompt=prompt,
            force_cloud=True,
        )
        model_alias = None
    else:
        # ── Automatic routing (Phase 3) ──────────────────────────
        routing_decision = await decision_engine.decide(profile)
        answer, used_provider, model_alias = await inference_router.complete_with_model(
            prompt=prompt,
            model_alias=routing_decision.selected_model,
        )

    provider_enum = (
        InferenceProvider.local
        if used_provider == ProviderResult.LOCAL
        else InferenceProvider.cloud
    )

    # ── Step 6: Cache write ──────────────────────────────────────
    await cache.set(prompt, answer)

    latency = (time.perf_counter() - start) * 1000
    return QueryResponse(
        answer=answer,
        provider=provider_enum,
        cached=False,
        sources=sources,
        latency_ms=round(latency, 2),
        model_alias=model_alias,
        classification=profile,
        routing_decision=routing_decision,
    )
