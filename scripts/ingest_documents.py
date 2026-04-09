"""
Document ingestion script.

Reads documents from a directory, chunks them, generates embeddings,
and indexes them into Qdrant.

Usage:
    python scripts/ingest_documents.py --input-dir ./sample-docs
    python scripts/ingest_documents.py --input-dir ./contracts --chunk-size 400

Supported formats: .txt, .md
(PDF support via PyMuPDF can be added — see Roadmap)
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retrieval.embedder import Embedder
from src.retrieval.qdrant_client import VectorStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 500   # characters
DEFAULT_CHUNK_OVERLAP = 50  # characters


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split text into overlapping chunks.

    Simple character-based chunking. For production, consider
    sentence-aware splitting (spaCy / NLTK) to avoid mid-sentence cuts.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]


def read_documents(input_dir: Path) -> list[dict]:
    """Read all supported documents from a directory."""
    supported = {".txt", ".md"}
    documents = []
    for path in sorted(input_dir.iterdir()):
        if path.suffix.lower() in supported:
            content = path.read_text(encoding="utf-8", errors="ignore")
            documents.append({"name": path.name, "content": content})
            logger.info("Read: %s (%d chars)", path.name, len(content))
    return documents


async def ingest(input_dir: Path, chunk_size: int, overlap: int) -> None:
    embedder = Embedder()
    store = VectorStore()
    await store.ensure_collection()

    documents = read_documents(input_dir)
    if not documents:
        logger.warning("No supported documents found in %s", input_dir)
        return

    total_chunks = 0
    for doc in documents:
        chunks = chunk_text(doc["content"], chunk_size, overlap)
        chunk_dicts = [
            {"document_name": doc["name"], "content": c, "chunk_index": i}
            for i, c in enumerate(chunks)
        ]
        vectors = embedder.embed([c["content"] for c in chunk_dicts])
        count = await store.upsert_chunks(chunk_dicts, vectors)
        total_chunks += count
        logger.info("Indexed %d chunks from %s", count, doc["name"])

    logger.info("Ingestion complete. Total chunks indexed: %d", total_chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into Qdrant.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing documents to ingest.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Characters per chunk (default: {DEFAULT_CHUNK_SIZE}).",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Chunk overlap in characters (default: {DEFAULT_CHUNK_OVERLAP}).",
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        logger.error("Input path is not a directory: %s", args.input_dir)
        sys.exit(1)

    asyncio.run(ingest(args.input_dir, args.chunk_size, args.overlap))


if __name__ == "__main__":
    main()
