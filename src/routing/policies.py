"""
Routing policies — the rule set that maps a QueryProfile to a model tier.

Each policy is a function that examines the QueryProfile and returns a
tier recommendation (or None if it doesn't apply). The Decision Engine
evaluates policies in priority order and picks the highest-priority match.

Policy priority (highest first):
    1. Sensitivity    — confidential → local-only (governance)
    2. Budget         — budget exceeded → downgrade to cheapest available
    3. Complexity     — high → premium, medium → standard, low → cheap
    4. Latency        — interactive → prefer fast tier
    5. Context size   — large → prefer long-context model
    6. Domain         — specialist domains may prefer specific vendors
    7. Confidence     — low confidence → upgrade one tier
"""

from src.models.classification import (
    Complexity,
    ContextSize,
    Domain,
    LatencyTier,
    QueryProfile,
    Sensitivity,
)


# Tier preference order from cheapest to most expensive.
TIER_ORDER = ["local", "cheap", "standard", "premium"]


def tier_index(tier: str) -> int:
    """Return the position of a tier in the cost ordering (0 = cheapest)."""
    try:
        return TIER_ORDER.index(tier)
    except ValueError:
        return 1  # default to "cheap" if unknown


def policy_sensitivity(profile: QueryProfile) -> str | None:
    """
    Governance policy: confidential data must stay on-premises.

    This is the highest-priority rule — it overrides cost and quality
    considerations to enforce data governance.
    """
    if profile.sensitivity == Sensitivity.CONFIDENTIAL:
        return "local"
    return None


def policy_budget_exceeded(budget_exceeded: bool) -> str | None:
    """
    FinOps policy: if the budget cap is hit, downgrade to the cheapest tier.

    This demonstrates cost-aware routing — a key enterprise concern.
    """
    if budget_exceeded:
        return "cheap"
    return None


def policy_complexity(profile: QueryProfile) -> str | None:
    """
    Core routing policy: map complexity to model tier.

    low    → cheap
    medium → standard
    high   → premium
    """
    if profile.complexity == Complexity.HIGH:
        return "premium"
    if profile.complexity == Complexity.MEDIUM:
        return "standard"
    if profile.complexity == Complexity.LOW:
        return "cheap"
    return None


def policy_latency(profile: QueryProfile) -> str | None:
    """
    Latency policy: interactive queries should prefer fast models.

    Only applies as a tiebreaker — doesn't override complexity-based
    selection, but caps the tier at "standard" for interactive queries
    unless complexity is high.
    """
    if profile.latency_tier == LatencyTier.INTERACTIVE and profile.complexity != Complexity.HIGH:
        return "standard"
    return None


def policy_context_size(profile: QueryProfile) -> str | None:
    """
    Context policy: large contexts need long-context models.

    Doesn't pick a tier directly, but signals that the engine should
    prefer models with large context windows within the chosen tier.
    """
    if profile.context_size == ContextSize.LARGE:
        return "large_context"
    return None


def policy_domain(profile: QueryProfile) -> str | None:
    """
    Domain policy: specialist domains may prefer specific vendors.

    For v1 this is informational — it adds a signal but doesn't
    override the tier. A future enhancement could map domains to
    specific model aliases (e.g. coding → Claude Sonnet).
    """
    if profile.domain == Domain.CODING:
        return "prefer_claude"
    if profile.domain == Domain.HEALTHCARE:
        return "prefer_local"
    return None


def policy_confidence(profile: QueryProfile) -> str | None:
    """
    Confidence policy: if the classifier is unsure, upgrade one tier.

    Low confidence (< 0.6) suggests the query is ambiguous and may
    benefit from a more capable model.
    """
    if profile.confidence < 0.6:
        return "upgrade"
    return None
