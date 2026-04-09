"""
FastAPI application entry point.

Registers routers, configures middleware, and exposes a /health
endpoint for container orchestration health checks.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local-First Hybrid AI Platform",
    description=(
        "Privacy-aware enterprise document intelligence using RAG, "
        "local-first inference, and semantic response caching."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/query", tags=["Query"])


@app.get("/health", tags=["System"])
async def health() -> dict:
    """Liveness probe for container orchestration."""
    return {"status": "ok"}


@app.get("/", tags=["System"])
async def root() -> dict:
    return {
        "service": "local-first-hybrid-ai-platform",
        "docs": "/docs",
        "health": "/health",
    }
