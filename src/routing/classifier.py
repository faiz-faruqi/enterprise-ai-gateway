"""
Query Classifier — produces a multi-dimensional QueryProfile for each query.

This is the first stage of the gateway's intelligent routing pipeline:

    User Query → [QueryClassifier] → QueryProfile → [DecisionEngine] → Model

The classifier is rule-based in v1 (no LLM call), making it fast (<1ms)
and deterministic. It analyses the query across six dimensions:

    1. Complexity      — low / medium / high
    2. Domain           — general / finance / healthcare / legal / coding / enterprise
    3. Sensitivity      — public / internal / confidential
    4. Context size     — small / medium / large
    5. RAG needed       — yes / no
    6. Latency tier     — interactive / batch

A confidence score (0.0–1.0) is also produced, which the Decision Engine
(Phase 3) and confidence-based routing (Phase 4) can use to decide whether
to upgrade to a more capable model.
"""

import logging

from src.models.classification import QueryProfile
from src.routing.rules import (
    classify_context_size,
    compute_confidence,
    detect_domain,
    detect_latency_tier,
    detect_rag_needed,
    detect_sensitivity,
    estimate_tokens,
    score_complexity,
)

logger = logging.getLogger(__name__)


class QueryClassifier:
    """
    Analyses a user query and produces a QueryProfile.

    Usage:
        classifier = QueryClassifier()
        profile = classifier.classify("Design a multi-cloud architecture for our bank.")
        # profile.complexity == Complexity.HIGH
        # profile.domain == Domain.ENTERPRISE
        # profile.sensitivity == Sensitivity.CONFIDENTIAL
    """

    def classify(
        self,
        query: str,
        context_chars: int = 0,
    ) -> QueryProfile:
        """
        Produce a QueryProfile for the given query.

        Args:
            query: The raw user query text.
            context_chars: The total character count of retrieved context
                           (if RAG has already run). Used for context-size
                           bucketing. Defaults to 0 (pre-RAG classification).

        Returns:
            A populated QueryProfile.
        """
        all_signals: list[str] = []

        # 1. Complexity
        complexity, signals = score_complexity(query)
        all_signals.extend(signals)

        # 2. Domain
        domain, signals = detect_domain(query)
        all_signals.extend(signals)

        # 3. Sensitivity
        sensitivity, signals = detect_sensitivity(query)
        all_signals.extend(signals)

        # 4. Context size
        context_size = classify_context_size(query, context_chars)
        all_signals.append(f"context:{context_size.value}")

        # 5. RAG needed
        rag_needed, signals = detect_rag_needed(query)
        all_signals.extend(signals)

        # 6. Latency tier
        latency_tier, signals = detect_latency_tier(query)
        all_signals.extend(signals)

        # Confidence
        confidence = compute_confidence(all_signals)

        # Token estimate
        token_estimate = estimate_tokens(query)

        profile = QueryProfile(
            complexity=complexity,
            domain=domain,
            sensitivity=sensitivity,
            context_size=context_size,
            rag_needed=rag_needed,
            latency_tier=latency_tier,
            confidence=confidence,
            token_estimate=token_estimate,
            signals=all_signals,
        )

        logger.info(
            "Classified query: complexity=%s domain=%s sensitivity=%s "
            "rag_needed=%s latency=%s confidence=%.2f tokens=%d",
            complexity.value, domain.value, sensitivity.value,
            rag_needed, latency_tier.value, confidence, token_estimate,
        )

        return profile
