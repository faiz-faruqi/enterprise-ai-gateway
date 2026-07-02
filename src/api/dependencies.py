"""
FastAPI dependency injection — shared component singletons.

All heavy objects (embedding model, vector store, Redis client,
inference router) are instantiated once at startup and reused
across requests via FastAPI's Depends() mechanism.

Usage in a router:
    from src.api.dependencies import get_embedder, get_vector_store_dep

    @router.post("/")
    async def query(
        request: QueryRequest,
        embedder: Embedder = Depends(get_embedder),
        store: VectorStoreType = Depends(get_vector_store_dep),
        cache: ResponseCache = Depends(get_cache),
        router: InferenceRouter = Depends(get_inference_router),
    ) -> QueryResponse:
        ...
"""

import logging
from functools import lru_cache

from src.cache.redis_cache import ResponseCache
from src.inference.ollama_client import OllamaClient
from src.inference.openrouter_client import OpenRouterClient
from src.inference.router import InferenceRouter
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store_factory import VectorStoreType, get_vector_store

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    """Singleton embedding model. Loaded once; reused across all requests."""
    logger.info("Initialising Embedder singleton.")
    return Embedder()


@lru_cache(maxsize=1)
def get_cache() -> ResponseCache:
    """Singleton Redis response cache."""
    logger.info("Initialising ResponseCache singleton.")
    return ResponseCache()


@lru_cache(maxsize=1)
def get_inference_router() -> InferenceRouter:
    """
    Singleton inference router with local (Ollama) and cloud (OpenRouter) clients.

    In DEMO_MODE, the 'local' client actually routes through OpenRouter using
    mistral-7b-instruct — documented in the UI and CLAUDE.md.
    """
    logger.info("Initialising InferenceRouter singleton.")
    return InferenceRouter(
        ollama=OllamaClient(),
        openrouter=OpenRouterClient(),
    )


def get_vector_store_dep() -> VectorStoreType:
    """
    Vector store dependency.

    Not cached with lru_cache because the pgvector client manages its own
    internal connection pool. A new instance per request is cheap since
    the pool is lazily initialised and reused internally.

    For Qdrant (local dev), the instance is also lightweight.
    """
    return get_vector_store()
