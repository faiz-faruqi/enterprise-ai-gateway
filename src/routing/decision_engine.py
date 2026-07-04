"""
Decision Engine — the gateway's intelligent model selection brain.

This is the core architectural component of the Enterprise AI Gateway.
It consumes a QueryProfile (from the Phase 2 classifier) and budget
state (from the BudgetTracker) and produces a RoutingDecision that
selects the optimal model and an ordered fallback chain.

The engine evaluates routing policies in priority order:

    1. Sensitivity (governance)   — confidential → local-only
    2. Budget (FinOps)            — exceeded → downgrade to cheapest
    3. Complexity (core routing)  — high→premium, medium→standard, low→cheap
    4. Latency                    — interactive → cap at standard
    5. Confidence                 — low confidence → upgrade one tier
    6. Domain / context           — vendor / context-window preferences

The selected tier is then mapped to a concrete model alias from the
ProviderRegistry, preferring models with the right characteristics
(large context, preferred vendor, etc.).
"""

import logging

from src.inference.provider_registry import ProviderRegistry
from src.models.classification import QueryProfile
from src.models.routing import RoutingDecision
from src.routing.budget import BudgetTracker
from src.routing.policies import (
    TIER_ORDER,
    policy_budget_exceeded,
    policy_complexity,
    policy_confidence,
    policy_context_size,
    policy_domain,
    policy_latency,
    policy_sensitivity,
    tier_index,
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Selects the optimal model for a query based on its QueryProfile.

    Usage:
        engine = DecisionEngine(registry, budget_tracker)
        decision = await engine.decide(profile)
        # decision.selected_model == "gpt-4o"
        # decision.reason == "complexity=high, budget_ok"
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        budget_tracker: BudgetTracker | None = None,
    ) -> None:
        self._registry = registry
        self._budget = budget_tracker

    async def decide(self, profile: QueryProfile) -> RoutingDecision:
        """
        Produce a RoutingDecision for the given query profile.

        This is the main entry point — called by the query endpoint
        when no explicit model is requested.
        """
        rules_matched: list[str] = []
        selected_tier: str | None = None
        prefer_large_context = False
        prefer_vendor: str | None = None

        # ── 1. Sensitivity (governance) — highest priority ────────────────
        tier = policy_sensitivity(profile)
        if tier:
            selected_tier = tier
            rules_matched.append(f"sensitivity={profile.sensitivity.value}→local")

        # ── 2. Budget (FinOps) ─────────────────────────────────────────────
        budget_exceeded = False
        budget_remaining: float | None = None
        if self._budget is not None and self._budget.has_budget_configured:
            budget_exceeded = await self._budget.is_budget_exceeded()
            budget_remaining = await self._budget.remaining_monthly()

        if selected_tier is None:
            tier = policy_budget_exceeded(budget_exceeded)
            if tier:
                selected_tier = tier
                rules_matched.append("budget_exceeded→cheap")

        # ── 3. Complexity (core routing) ───────────────────────────────────
        if selected_tier is None:
            tier = policy_complexity(profile)
            if tier:
                selected_tier = tier
                rules_matched.append(f"complexity={profile.complexity.value}→{tier}")

        # Fallback to "standard" if no policy fired.
        if selected_tier is None:
            selected_tier = "standard"
            rules_matched.append("default→standard")

        # ── 4. Latency (tiebreaker / cap) ──────────────────────────────────
        latency_tier = policy_latency(profile)
        if latency_tier and latency_tier != "large_context":
            # Cap at "standard" for interactive non-complex queries.
            if tier_index(selected_tier) > tier_index("standard"):
                selected_tier = "standard"
                rules_matched.append(f"latency=interactive→cap@standard")

        # ── 5. Confidence (upgrade) ────────────────────────────────────────
        confidence_signal = policy_confidence(profile)
        if confidence_signal == "upgrade":
            current_idx = tier_index(selected_tier)
            if current_idx < len(TIER_ORDER) - 1:
                selected_tier = TIER_ORDER[current_idx + 1]
                rules_matched.append(
                    f"confidence={profile.confidence:.2f}<0.6→upgrade_to_{selected_tier}"
                )

        # ── 6. Context size & domain preferences ───────────────────────────
        context_signal = policy_context_size(profile)
        if context_signal == "large_context":
            prefer_large_context = True
            rules_matched.append("context=large→prefer_long_context")

        domain_signal = policy_domain(profile)
        if domain_signal == "prefer_claude":
            prefer_vendor = "anthropic"
            rules_matched.append("domain=coding→prefer_anthropic")
        elif domain_signal == "prefer_local":
            # Healthcare → prefer local for privacy.
            if self._registry.local_providers():
                selected_tier = "local"
                rules_matched.append("domain=healthcare→prefer_local")
            prefer_vendor = None

        # ── Select concrete model from registry ────────────────────────────
        selected_model = self._select_model(
            selected_tier,
            prefer_large_context=prefer_large_context,
            prefer_vendor=prefer_vendor,
        )

        # ── Build fallback chain ───────────────────────────────────────────
        fallback_chain = self._build_fallback_chain(selected_model, selected_tier)

        # ── Estimate cost ──────────────────────────────────────────────────
        provider = self._registry.get(selected_model)
        estimated_cost = 0.0
        if provider:
            # Rough estimate: assume ~500 input + ~200 output tokens.
            estimated_cost = (
                provider.info.cost_per_1k_input * 0.5
                + provider.info.cost_per_1k_output * 0.2
            )

        reason = ", ".join(rules_matched) if rules_matched else "default"

        logger.info(
            "Decision: model=%s tier=%s reason='%s' fallback=%s cost=$%.6f",
            selected_model, selected_tier, reason, fallback_chain, estimated_cost,
        )

        return RoutingDecision(
            selected_model=selected_model,
            selected_tier=selected_tier,
            reason=reason,
            fallback_chain=fallback_chain,
            estimated_cost=round(estimated_cost, 6),
            budget_remaining=round(budget_remaining, 4) if budget_remaining is not None else None,
            rules_matched=rules_matched,
        )

    def _select_model(
        self,
        tier: str,
        prefer_large_context: bool = False,
        prefer_vendor: str | None = None,
    ) -> str:
        """
        Pick a concrete model alias for the given tier.

        Applies preferences for context window and vendor when available.
        Falls back to the first model in the tier if no preference match.
        """
        candidates = self._registry.by_tier(tier)
        if not candidates:
            # If the tier is empty (e.g. no local models in DEMO_MODE),
            # fall back to "cheap" then "standard".
            for fallback_tier in ("cheap", "standard"):
                candidates = self._registry.by_tier(fallback_tier)
                if candidates:
                    break

        if not candidates:
            # Ultimate fallback — any cloud model.
            candidates = self._registry.cloud_providers()

        if not candidates:
            raise RuntimeError("No providers available in the registry.")

        # Apply vendor preference.
        if prefer_vendor:
            vendor_matches = [p for p in candidates if p.info.vendor == prefer_vendor]
            if vendor_matches:
                candidates = vendor_matches

        # Apply context-window preference (prefer largest).
        if prefer_large_context:
            candidates = sorted(candidates, key=lambda p: p.info.context_window, reverse=True)

        return candidates[0].alias

    def _build_fallback_chain(self, selected_model: str, selected_tier: str) -> list[str]:
        """
        Build an ordered fallback list for resilience.

        Strategy: same-tier alternatives first, then progressively cheaper
        tiers, then local models as a last resort.
        """
        chain: list[str] = []
        selected_provider = self._registry.get(selected_model)

        # Same-tier alternatives (different vendor).
        for provider in self._registry.by_tier(selected_tier):
            if provider.alias != selected_model:
                chain.append(provider.alias)

        # Cheaper tiers.
        current_idx = tier_index(selected_tier)
        for i in range(current_idx - 1, -1, -1):
            tier = TIER_ORDER[i]
            for provider in self._registry.by_tier(tier):
                if provider.alias not in chain and provider.alias != selected_model:
                    chain.append(provider.alias)

        # Local models as last resort (if not already included).
        for provider in self._registry.local_providers():
            if provider.alias not in chain and provider.alias != selected_model:
                chain.append(provider.alias)

        return chain[:5]  # cap at 5 fallbacks
