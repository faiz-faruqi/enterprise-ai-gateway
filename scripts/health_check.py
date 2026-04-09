"""
Platform health check script.

Validates connectivity to all platform components and prints a status table.

Usage:
    python scripts/health_check.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


async def check_http(name: str, url: str) -> tuple[str, bool, str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            ok = resp.status_code < 400
            return name, ok, f"HTTP {resp.status_code}"
    except Exception as exc:
        return name, False, str(exc)


async def check_redis() -> tuple[str, bool, str]:
    try:
        import redis.asyncio as aioredis
        client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        result = await client.ping()
        return "Redis", result, "PONG" if result else "No response"
    except Exception as exc:
        return "Redis", False, str(exc)


async def run_checks() -> None:
    checks = await asyncio.gather(
        check_http("FastAPI", f"{FASTAPI_URL}/health"),
        check_http("Qdrant", f"{QDRANT_URL}/healthz"),
        check_http("Ollama", f"{OLLAMA_URL}/api/tags"),
        check_http("Open WebUI", "http://localhost:3000"),
        check_redis(),
    )

    print("\n── Platform Health Check ────────────────────────────")
    print(f"{'Component':<20} {'Status':<10} {'Detail'}")
    print("─" * 55)
    all_ok = True
    for name, ok, detail in checks:
        status = "✓ OK" if ok else "✗ FAIL"
        print(f"{name:<20} {status:<10} {detail}")
        if not ok:
            all_ok = False
    print("─" * 55)
    print("All systems operational.\n" if all_ok else "One or more components unreachable.\n")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    asyncio.run(run_checks())
