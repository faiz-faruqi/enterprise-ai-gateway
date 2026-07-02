"""
Unit tests for ResponseCache.

All Redis operations are mocked — no live Redis required.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.cache.redis_cache import ResponseCache


class TestResponseCache:
    @pytest.fixture
    def cache(self, mock_redis_client):
        """ResponseCache instance with an injected mock Redis client."""
        with patch("src.cache.redis_cache.aioredis.Redis", return_value=mock_redis_client):
            instance = ResponseCache(redis_url="", host="localhost", port=6379)
            instance._client = mock_redis_client
            return instance, mock_redis_client

    async def test_cache_miss_returns_none(self, cache):
        instance, mock_client = cache
        mock_client.get.return_value = None
        result = await instance.get("some prompt")
        assert result is None

    async def test_cache_hit_returns_value(self, cache):
        instance, mock_client = cache
        mock_client.get.return_value = "Cached answer text."
        result = await instance.get("some prompt")
        assert result == "Cached answer text."

    async def test_set_calls_setex(self, cache):
        instance, mock_client = cache
        await instance.set("some prompt", "response text")
        mock_client.setex.assert_called_once()
        # Key, TTL, value
        call_args = mock_client.setex.call_args[0]
        assert call_args[1] == instance._ttl  # TTL as second arg
        assert call_args[2] == "response text"

    async def test_cache_key_is_deterministic(self, cache):
        instance, _ = cache
        key1 = instance._make_key("hello world")
        key2 = instance._make_key("hello world")
        key3 = instance._make_key("different prompt")
        assert key1 == key2
        assert key1 != key3

    async def test_cache_key_has_prefix(self, cache):
        instance, _ = cache
        key = instance._make_key("any prompt")
        assert key.startswith("llm:response:")

    async def test_cache_read_failure_returns_none_gracefully(self, cache):
        """Redis failure during read should not raise — return None silently."""
        instance, mock_client = cache
        mock_client.get.side_effect = ConnectionError("Redis down")
        result = await instance.get("some prompt")
        assert result is None

    async def test_cache_write_failure_does_not_raise(self, cache):
        """Redis failure during write should be swallowed gracefully."""
        instance, mock_client = cache
        mock_client.setex.side_effect = ConnectionError("Redis down")
        # Should not raise
        await instance.set("some prompt", "some response")

    async def test_flush_returns_zero_when_no_keys(self, cache):
        instance, mock_client = cache
        mock_client.keys.return_value = []
        result = await instance.flush()
        assert result == 0

    async def test_flush_deletes_matching_keys(self, cache):
        instance, mock_client = cache
        mock_client.keys.return_value = ["llm:response:abc", "llm:response:def"]
        mock_client.delete.return_value = 2
        result = await instance.flush()
        assert result == 2
        mock_client.delete.assert_called_once()

    async def test_health_check_returns_true_when_redis_ok(self, cache):
        instance, mock_client = cache
        mock_client.ping.return_value = True
        result = await instance.health_check()
        assert result is True

    async def test_health_check_returns_false_when_redis_down(self, cache):
        instance, mock_client = cache
        mock_client.ping.side_effect = ConnectionError("Redis down")
        result = await instance.health_check()
        assert result is False
