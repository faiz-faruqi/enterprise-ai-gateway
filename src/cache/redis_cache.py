"""
Redis response cache.

Implements ADR 0002: cache LLM responses keyed by the grounded prompt.

Key design choices:
- Cache key is an MD5 hash of the full prompt string (including retrieved context),
  not just the user's raw query. This ensures cache entries are context-sensitive —
  the same question over a different document set will not return a stale answer.
- TTL is configurable via CACHE_TTL_SECONDS (default: 3600s).
- Cache invalidation is manual: if documents are re-indexed, flush the cache.
- Accepts either REDIS_URL (Railway / cloud) or REDIS_HOST + REDIS_PORT (local/Docker).
"""

import hashlib
import logging
import os
from typing import Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

CACHE_KEY_PREFIX = "llm:response:"


class ResponseCache:
    """
    Async Redis client for prompt-response caching.

    Automatically prefers REDIS_URL (connection string) when set —
    required for Railway's managed Redis add-on. Falls back to
    REDIS_HOST + REDIS_PORT for local Docker Compose usage.

    Usage:
        cache = ResponseCache()
        cached = await cache.get(prompt)
        if cached:
            return cached
        response = await llm.complete(prompt)
        await cache.set(prompt, response)
    """

    def __init__(
        self,
        redis_url: str = REDIS_URL,
        host: str = REDIS_HOST,
        port: int = REDIS_PORT,
        ttl: int = CACHE_TTL_SECONDS,
    ) -> None:
        if redis_url:
            self._client = aioredis.from_url(redis_url, decode_responses=True)
            logger.info("Redis cache initialised via REDIS_URL.")
        else:
            self._client = aioredis.Redis(host=host, port=port, decode_responses=True)
            logger.info("Redis cache initialised via host=%s port=%d.", host, port)
        self._ttl = ttl

    def _make_key(self, prompt: str) -> str:
        """
        Derive a stable cache key from the prompt.

        MD5 is used here for speed — this is not a security hash,
        just a compact key for cache lookup.
        """
        digest = hashlib.md5(prompt.encode()).hexdigest()  # noqa: S324
        return f"{CACHE_KEY_PREFIX}{digest}"

    async def get(self, prompt: str) -> Optional[str]:
        """Return a cached response or None on cache miss."""
        key = self._make_key(prompt)
        try:
            value = await self._client.get(key)
            if value:
                logger.info("Cache hit for key %s.", key[:20])
            return value
        except Exception as exc:
            logger.warning("Cache read failed: %s", exc)
            return None

    async def set(self, prompt: str, response: str) -> None:
        """Write a response to cache with the configured TTL."""
        key = self._make_key(prompt)
        try:
            await self._client.setex(key, self._ttl, response)
            logger.info("Cached response at key %s (TTL=%ds).", key[:20], self._ttl)
        except Exception as exc:
            logger.warning("Cache write failed: %s", exc)

    async def flush(self, pattern: str = f"{CACHE_KEY_PREFIX}*") -> int:
        """Flush all cache entries matching a key pattern. Returns count deleted."""
        keys = await self._client.keys(pattern)
        if keys:
            return await self._client.delete(*keys)
        return 0

    async def health_check(self) -> bool:
        """Return True if Redis is reachable."""
        try:
            return await self._client.ping()
        except Exception:
            return False
