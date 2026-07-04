"""
Declarative model catalog for the Enterprise AI Gateway.

Each entry describes a model the gateway can route to, including its
vendor, cost characteristics, context window, and deployment tier.

This catalog is the single source of truth for the ProviderRegistry.
Adding a new model = adding one entry here. No code changes elsewhere.

Tiers (used by the Decision Engine in Phase 3):
    - local     : on-premises inference (privacy-sensitive workloads)
    - cheap     : low-cost cloud model for simple queries
    - standard  : balanced cost/quality cloud model
    - premium   : high-reasoning cloud model for complex queries

Latency tiers:
    - fast      : sub-second first-token latency
    - balanced  : 1-3s typical
    - slow      : deep reasoning, 3s+
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelDefinition:
    """Static description of a routable model."""

    alias: str            # short name used in API requests, e.g. "gpt-4o"
    vendor: str           # "openai" | "anthropic" | "google" | "meta" | "local"
    model_id: str         # provider-native model id, e.g. "openai/gpt-4o"
    tier: str             # "local" | "cheap" | "standard" | "premium"
    context_window: int   # max tokens the model accepts
    cost_per_1k_input: float   # USD per 1k input tokens (0.0 for local)
    cost_per_1k_output: float  # USD per 1k output tokens (0.0 for local)
    latency_tier: str     # "fast" | "balanced" | "slow"
    is_local: bool        # True => runs on-premises (Ollama), no external API
    description: str


# ── Catalog ──────────────────────────────────────────────────────────────────
# Costs are approximate public list prices in USD per 1k tokens as of 2025.
# Local models have zero per-token cost (compute is sunk/owned).

MODEL_CATALOG: dict[str, ModelDefinition] = {
    # ── Local (Ollama) ────────────────────────────────────────────────────────
    "local-gemma": ModelDefinition(
        alias="local-gemma",
        vendor="google",
        model_id="gemma2:9b",
        tier="local",
        context_window=8192,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        latency_tier="balanced",
        is_local=True,
        description="Gemma 2 9B running on local Ollama node. Privacy-first, zero token cost.",
    ),
    "local-llama": ModelDefinition(
        alias="local-llama",
        vendor="meta",
        model_id="llama3.1:8b",
        tier="local",
        context_window=128000,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        latency_tier="balanced",
        is_local=True,
        description="Llama 3.1 8B on local Ollama. Long context, on-premises.",
    ),

    # ── Cheap tier ────────────────────────────────────────────────────────────
    "gpt-4o-mini": ModelDefinition(
        alias="gpt-4o-mini",
        vendor="openai",
        model_id="openai/gpt-4o-mini",
        tier="cheap",
        context_window=128000,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        latency_tier="fast",
        is_local=False,
        description="OpenAI GPT-4o mini. Fast and inexpensive for simple queries.",
    ),
    "claude-haiku": ModelDefinition(
        alias="claude-haiku",
        vendor="anthropic",
        model_id="anthropic/claude-3-haiku",
        tier="cheap",
        context_window=200000,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        latency_tier="fast",
        is_local=False,
        description="Anthropic Claude 3 Haiku. Fast, low-cost, large context.",
    ),
    "gemini-flash": ModelDefinition(
        alias="gemini-flash",
        vendor="google",
        model_id="google/gemini-flash-1.5",
        tier="cheap",
        context_window=1000000,
        cost_per_1k_input=0.000075,
        cost_per_1k_output=0.0003,
        latency_tier="fast",
        is_local=False,
        description="Google Gemini 1.5 Flash. Very cheap, huge context window.",
    ),

    # ── Standard tier ────────────────────────────────────────────────────────
    "gpt-4o": ModelDefinition(
        alias="gpt-4o",
        vendor="openai",
        model_id="openai/gpt-4o",
        tier="standard",
        context_window=128000,
        cost_per_1k_input=0.005,
        cost_per_1k_output=0.015,
        latency_tier="balanced",
        is_local=False,
        description="OpenAI GPT-4o. Balanced quality and cost for general enterprise tasks.",
    ),
    "claude-sonnet": ModelDefinition(
        alias="claude-sonnet",
        vendor="anthropic",
        model_id="anthropic/claude-3.5-sonnet",
        tier="standard",
        context_window=200000,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        latency_tier="balanced",
        is_local=False,
        description="Anthropic Claude 3.5 Sonnet. Strong reasoning and coding.",
    ),
    "gemini-pro": ModelDefinition(
        alias="gemini-pro",
        vendor="google",
        model_id="google/gemini-pro-1.5",
        tier="standard",
        context_window=2000000,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        latency_tier="balanced",
        is_local=False,
        description="Google Gemini 1.5 Pro. Massive context, multimodal.",
    ),

    # ── Premium tier ──────────────────────────────────────────────────────────
    "gpt-5": ModelDefinition(
        alias="gpt-5",
        vendor="openai",
        model_id="openai/gpt-5",
        tier="premium",
        context_window=256000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        latency_tier="slow",
        is_local=False,
        description="OpenAI GPT-5. Highest reasoning quality for complex architecture queries.",
    ),
    "claude-opus": ModelDefinition(
        alias="claude-opus",
        vendor="anthropic",
        model_id="anthropic/claude-3-opus",
        tier="premium",
        context_window=200000,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        latency_tier="slow",
        is_local=False,
        description="Anthropic Claude 3 Opus. Deep reasoning for complex analysis.",
    ),
}


def list_models() -> list[ModelDefinition]:
    """Return all registered model definitions."""
    return list(MODEL_CATALOG.values())


def get_model(alias: str) -> ModelDefinition | None:
    """Look up a model definition by its alias."""
    return MODEL_CATALOG.get(alias)
