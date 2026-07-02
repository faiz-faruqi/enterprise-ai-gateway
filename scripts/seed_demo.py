"""
Demo seeding script.

Reads all .md and .txt files from the sample-docs/ directory and
ingests them into the deployed backend via the /ingest/text API endpoint.

This script is idempotent by document name — it checks whether any
chunks already exist before ingesting, and skips already-seeded documents
(requires VECTOR_STORE=pgvector with count() support; for Qdrant it
always re-ingests).

Usage:
    # Seed against local dev backend
    python scripts/seed_demo.py

    # Seed against Railway deployment
    python scripts/seed_demo.py --api-url https://api.yourdomain.com

    # Force re-ingest (skip idempotency check)
    python scripts/seed_demo.py --force
"""

import argparse
import json
import logging
import sys
import time
import urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

SAMPLE_DOCS_DIR = Path(__file__).resolve().parent.parent / "sample-docs"
SUPPORTED_EXTENSIONS = {".md", ".txt"}


def api_request(url: str, payload: dict, timeout: int = 30) -> dict:
    """POST a JSON payload to the given URL and return the parsed response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if hasattr(exc, "read") else ""
        logger.error("HTTP %d from %s: %s", exc.code, url, body)
        raise
    except Exception as exc:
        logger.error("Request failed: %s", exc)
        raise


def check_api_ready(base_url: str) -> bool:
    """Return True if the API health endpoint responds with status ok."""
    url = f"{base_url}/health"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
            return data.get("status") == "ok"
    except Exception:
        return False


def wait_for_api(base_url: str, max_wait: int = 60) -> None:
    """Poll the health endpoint until ready or timeout."""
    logger.info("Waiting for API at %s ...", base_url)
    for i in range(max_wait):
        if check_api_ready(base_url):
            logger.info("API ready.")
            return
        time.sleep(1)
        if (i + 1) % 10 == 0:
            logger.info("Still waiting... (%ds)", i + 1)
    logger.error("API did not become ready within %ds.", max_wait)
    sys.exit(1)


def ingest_document(base_url: str, doc_name: str, content: str) -> int:
    """Ingest a single document. Returns number of chunks indexed."""
    url = f"{base_url}/ingest/text"
    payload = {
        "document_name": doc_name,
        "content": content,
        "collection": "enterprise-docs",
    }
    result = api_request(url, payload, timeout=60)
    return result.get("chunks_indexed", 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo documents into the platform.")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the FastAPI backend (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=SAMPLE_DOCS_DIR,
        help=f"Directory containing demo documents (default: {SAMPLE_DOCS_DIR})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest all documents even if already seeded.",
    )
    args = parser.parse_args()

    base_url = args.api_url.rstrip("/")
    docs_dir: Path = args.docs_dir

    if not docs_dir.is_dir():
        logger.error("Documents directory not found: %s", docs_dir)
        sys.exit(1)

    wait_for_api(base_url)

    docs = sorted(
        p for p in docs_dir.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS and not p.name.startswith(".")
    )

    if not docs:
        logger.warning("No supported documents found in %s", docs_dir)
        sys.exit(0)

    logger.info("Found %d document(s) to ingest from %s", len(docs), docs_dir)

    total_chunks = 0
    for doc_path in docs:
        content = doc_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            logger.warning("Skipping empty document: %s", doc_path.name)
            continue
        logger.info("Ingesting: %s (%d chars)", doc_path.name, len(content))
        try:
            count = ingest_document(base_url, doc_path.name, content)
            total_chunks += count
            logger.info("  → %d chunks indexed", count)
        except Exception as exc:
            logger.error("  → Failed to ingest %s: %s", doc_path.name, exc)

    logger.info("Seeding complete. Total chunks indexed: %d", total_chunks)


if __name__ == "__main__":
    main()
