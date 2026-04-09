"""
Request and response schemas.

Using Pydantic v2 for runtime validation and auto-generated OpenAPI docs.
"""

from enum import Enum

from pydantic import BaseModel, Field


class InferenceProvider(str, Enum):
    """Which inference provider handled the request."""
    local = "local"
    cloud = "cloud"
    cache = "cache"


class QueryRequest(BaseModel):
    """Incoming user query payload."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language question over enterprise documents.",
        examples=["What are the termination conditions in the vendor contract?"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of document chunks to retrieve from the vector store.",
    )
    force_cloud: bool = Field(
        default=False,
        description="Bypass local inference and use cloud provider directly.",
    )


class SourceDocument(BaseModel):
    """A retrieved document chunk included as context."""

    chunk_id: str
    document_name: str
    content_preview: str = Field(..., max_length=300)
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class QueryResponse(BaseModel):
    """Response returned to the user."""

    answer: str
    provider: InferenceProvider
    cached: bool
    sources: list[SourceDocument]
    latency_ms: float


class IngestRequest(BaseModel):
    """Request to ingest a document into the vector store."""

    document_name: str
    content: str
    collection: str = Field(default="enterprise-docs")


class IngestResponse(BaseModel):
    chunks_indexed: int
    collection: str
    document_name: str
