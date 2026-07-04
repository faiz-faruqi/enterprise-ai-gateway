"""
Query classification schemas.

A `QueryProfile` is the multi-dimensional analysis of an incoming query
produced by the QueryClassifier (Phase 2). It is consumed by the Decision
Engine (Phase 3) to select the optimal model.

Dimensions:
  - complexity:      low | medium | high
  - domain:          general | finance | healthcare | legal | coding | enterprise
  - sensitivity:     public | internal | confidential
  - context_size:    small | medium | large
  - rag_needed:      bool
  - latency_tier:    interactive | batch
  - confidence:      0.0–1.0 (classifier self-assessed)
"""

from enum import Enum

from pydantic import BaseModel, Field


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Domain(str, Enum):
    GENERAL = "general"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    CODING = "coding"
    ENTERPRISE = "enterprise"


class Sensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"


class ContextSize(str, Enum):
    SMALL = "small"      # < 500 chars
    MEDIUM = "medium"    # 500–2000 chars
    LARGE = "large"      # > 2000 chars


class LatencyTier(str, Enum):
    INTERACTIVE = "interactive"
    BATCH = "batch"


class QueryProfile(BaseModel):
    """
    Multi-dimensional analysis of a user query.

    Every field is derived from the raw query text (and optionally the
    retrieved context) by the QueryClassifier — no LLM call is required
    for the rule-based v1 implementation.
    """

    model_config = {"protected_namespaces": ()}

    complexity: Complexity = Field(
        description="Estimated reasoning difficulty of the query."
    )
    domain: Domain = Field(
        description="Detected subject-matter domain."
    )
    sensitivity: Sensitivity = Field(
        description="Data sensitivity classification for governance routing."
    )
    context_size: ContextSize = Field(
        description="Size bucket of the query + retrieved context."
    )
    rag_needed: bool = Field(
        description="Whether enterprise document retrieval is needed."
    )
    latency_tier: LatencyTier = Field(
        description="Latency expectation: interactive (fast) or batch (slow OK)."
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Classifier self-confidence in its assessment (0.0–1.0).",
    )
    token_estimate: int = Field(
        ge=0,
        description="Rough token count estimate for the query text.",
    )
    signals: list[str] = Field(
        default_factory=list,
        description="Human-readable list of classification signals detected.",
    )
