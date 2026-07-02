"""
Integration-style tests for the POST /query/ endpoint.

Uses FastAPI TestClient with all external dependencies mocked via
dependency_overrides — no real Redis, Qdrant, or LLM calls are made.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import (
    get_cache,
    get_embedder,
    get_inference_router,
    get_vector_store_dep,
)
from src.inference.router import ProviderResult


def make_mock_hit(doc_name: str, content: str, score: float = 0.88):
    """Build a mock vector search result."""
    hit = MagicMock()
    hit.score = score
    hit.payload = {
        "chunk_id": "test-chunk-001",
        "document_name": doc_name,
        "content": content,
        "chunk_index": 0,
    }
    return hit


@pytest.fixture
def mock_embedder():
    m = MagicMock()
    m.embed_single.return_value = [0.1] * 384
    return m


@pytest.fixture
def mock_store():
    m = AsyncMock()
    m.search = AsyncMock(
        return_value=[
            make_mock_hit(
                "sample-vendor-contract.md",
                "Either party may terminate this agreement with 90 days written notice.",
                0.91,
            )
        ]
    )
    return m


@pytest.fixture
def mock_cache():
    m = AsyncMock()
    m.get = AsyncMock(return_value=None)
    m.set = AsyncMock()
    return m


@pytest.fixture
def mock_router(mock_ollama, mock_openrouter):
    from src.inference.router import InferenceRouter
    return InferenceRouter(ollama=mock_ollama, openrouter=mock_openrouter)


@pytest.fixture
def client(mock_embedder, mock_store, mock_cache, mock_router):
    """TestClient with all dependencies overridden."""
    app.dependency_overrides[get_embedder] = lambda: mock_embedder
    app.dependency_overrides[get_vector_store_dep] = lambda: mock_store
    app.dependency_overrides[get_cache] = lambda: mock_cache
    app.dependency_overrides[get_inference_router] = lambda: mock_router
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestQueryEndpoint:
    def test_query_returns_200_with_local_provider(self, client, mock_cache, mock_ollama):
        mock_cache.get.return_value = None  # cache miss
        response = client.post(
            "/query/",
            json={"query": "What are the termination conditions?", "top_k": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "local"
        assert data["cached"] is False
        assert len(data["sources"]) == 1
        assert "latency_ms" in data
        assert isinstance(data["answer"], str)

    def test_query_returns_cached_response(self, client, mock_cache):
        mock_cache.get.return_value = "This is a cached answer."
        response = client.post(
            "/query/",
            json={"query": "What are the termination conditions?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "cache"
        assert data["cached"] is True
        assert data["answer"] == "This is a cached answer."

    def test_query_force_cloud_routes_to_cloud(self, client, mock_cache, mock_ollama, mock_openrouter):
        mock_cache.get.return_value = None
        response = client.post(
            "/query/",
            json={"query": "Complex multi-hop reasoning query", "force_cloud": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "cloud"
        mock_ollama.complete.assert_not_called()

    def test_query_returns_404_when_no_docs(self, mock_embedder, mock_cache, mock_router):
        """When vector search returns empty results, endpoint returns 404."""
        empty_store = AsyncMock()
        empty_store.search = AsyncMock(return_value=[])
        app.dependency_overrides[get_embedder] = lambda: mock_embedder
        app.dependency_overrides[get_vector_store_dep] = lambda: empty_store
        app.dependency_overrides[get_cache] = lambda: mock_cache
        app.dependency_overrides[get_inference_router] = lambda: mock_router
        with TestClient(app) as c:
            response = c.post("/query/", json={"query": "Any question"})
        app.dependency_overrides.clear()
        assert response.status_code == 404

    def test_query_validates_min_length(self, client):
        """Query shorter than 3 chars should be rejected by Pydantic."""
        response = client.post("/query/", json={"query": "ab"})
        assert response.status_code == 422

    def test_query_validates_max_top_k(self, client):
        """top_k > 20 should be rejected."""
        response = client.post(
            "/query/",
            json={"query": "Valid question text", "top_k": 99},
        )
        assert response.status_code == 422

    def test_health_endpoint_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "service" in response.json()
