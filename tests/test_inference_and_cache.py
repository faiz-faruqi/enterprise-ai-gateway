"""
Unit tests for the inference router and response cache.

These tests mock external dependencies (Ollama, OpenRouter, Redis)
so they run cleanly in CI without any live services.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.inference.router import InferenceRouter, ProviderResult


# ── InferenceRouter Tests ────────────────────────────────────────────────────


class TestInferenceRouter:

    @pytest.fixture
    def ollama_mock(self):
        m = AsyncMock()
        m.complete = AsyncMock(return_value="Local model answer.")
        return m

    @pytest.fixture
    def openrouter_mock(self):
        m = AsyncMock()
        m.complete = AsyncMock(return_value="Cloud model answer.")
        return m

    @pytest.fixture
    def router(self, ollama_mock, openrouter_mock):
        return InferenceRouter(ollama=ollama_mock, openrouter=openrouter_mock)

    async def test_primary_path_uses_ollama(self, router, ollama_mock, openrouter_mock):
        answer, provider = await router.complete("Test prompt")
        assert provider == ProviderResult.LOCAL
        assert answer == "Local model answer."
        ollama_mock.complete.assert_called_once()
        openrouter_mock.complete.assert_not_called()

    async def test_fallback_on_ollama_failure(self, router, ollama_mock, openrouter_mock):
        ollama_mock.complete.side_effect = ConnectionError("Ollama unreachable")
        answer, provider = await router.complete("Test prompt")
        assert provider == ProviderResult.CLOUD
        assert answer == "Cloud model answer."

    async def test_force_cloud_bypasses_ollama(self, router, ollama_mock, openrouter_mock):
        answer, provider = await router.complete("Test prompt", force_cloud=True)
        assert provider == ProviderResult.CLOUD
        ollama_mock.complete.assert_not_called()


# ── ResponseCache Tests ──────────────────────────────────────────────────────


class TestResponseCache:

    @pytest.fixture
    def cache(self):
        with patch("src.cache.redis_cache.aioredis.Redis") as mock_redis_cls:
            mock_client = AsyncMock()
            mock_redis_cls.return_value = mock_client

            from src.cache.redis_cache import ResponseCache
            c = ResponseCache()
            c._client = mock_client
            return c, mock_client

    async def test_cache_miss_returns_none(self, cache):
        instance, mock_client = cache
        mock_client.get = AsyncMock(return_value=None)
        result = await instance.get("some prompt")
        assert result is None

    async def test_cache_hit_returns_value(self, cache):
        instance, mock_client = cache
        mock_client.get = AsyncMock(return_value="Cached answer.")
        result = await instance.get("some prompt")
        assert result == "Cached answer."

    async def test_set_calls_setex(self, cache):
        instance, mock_client = cache
        mock_client.setex = AsyncMock()
        await instance.set("some prompt", "response text")
        mock_client.setex.assert_called_once()

    async def test_cache_key_is_deterministic(self, cache):
        instance, _ = cache
        key1 = instance._make_key("hello world")
        key2 = instance._make_key("hello world")
        key3 = instance._make_key("different prompt")
        assert key1 == key2
        assert key1 != key3

    async def test_redis_failure_returns_none_gracefully(self, cache):
        instance, mock_client = cache
        mock_client.get = AsyncMock(side_effect=ConnectionError("Redis down"))
        result = await instance.get("some prompt")
        assert result is None
