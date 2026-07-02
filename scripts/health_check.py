"""
Platform health check script.

Verifies that all components of the platform are reachable and operational:
  - FastAPI /health endpoint
  - Redis (via the API health response)
  - Vector store (Qdrant or pgvector, via the API health response)
  - Ollama (optional — only checked if OLLAMA_BASE_URL is configured)

Usage:
    python scripts/health_check.py
    python scripts/health_check.py --api-url http://localhost:8000
    python scripts/health_check.py --api-url https://api.yourdomain.com

Exit codes:
    0 — all components healthy
    1 — one or more components unreachable or reporting errors
"""

import argparse
import json
import sys
import urllib.request
from typing import Any


def check_health(api_url: str) -> dict[str, Any]:
    """Call the FastAPI /health endpoint and return the parsed JSON response."""
    url = f"{api_url.rstrip('/')}/health"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except Exception as exc:
        print(f"[FAIL] Cannot reach {url}: {exc}", file=sys.stderr)
        sys.exit(1)


def print_status(label: str, status: str) -> bool:
    """Print a status line. Returns True if healthy, False otherwise."""
    is_ok = status == "ok"
    symbol = "OK  " if is_ok else "FAIL"
    print(f"  [{symbol}] {label}: {status}")
    return is_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Check platform component health.")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the FastAPI backend (default: http://localhost:8000)",
    )
    args = parser.parse_args()

    print(f"\nChecking platform health at: {args.api_url}\n")
    health = check_health(args.api_url)

    all_ok = True

    # Top-level status
    top = health.get("status", "unknown")
    ok = print_status("API", top)
    all_ok = all_ok and ok

    # Metadata
    print(f"\n  version     : {health.get('version', 'unknown')}")
    print(f"  vector_store: {health.get('vector_store', 'unknown')}")
    print(f"  demo_mode   : {health.get('demo_mode', False)}")
    print()

    # Component statuses
    components = health.get("components", {})
    if components:
        print("  Components:")
        for component, status in components.items():
            ok = print_status(f"  {component}", status)
            all_ok = all_ok and ok
    else:
        print("  No component details returned.")

    print()
    if all_ok:
        print("All components healthy.\n")
        sys.exit(0)
    else:
        print("One or more components are unhealthy. Check logs above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
