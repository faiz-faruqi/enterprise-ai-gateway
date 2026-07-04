"""
Tests for the Phase 2 Query Classifier.

Verifies that the classifier correctly identifies complexity, domain,
sensitivity, RAG need, latency tier, and context size across a range of
representative enterprise queries.
"""

import pytest

from src.models.classification import (
    Complexity,
    ContextSize,
    Domain,
    LatencyTier,
    Sensitivity,
)
from src.routing.classifier import QueryClassifier
from src.routing.rules import estimate_tokens


class TestQueryClassifier:
    @pytest.fixture
    def classifier(self):
        return QueryClassifier()

    # ── Complexity ───────────────────────────────────────────────────────────

    def test_simple_factual_query_is_low_complexity(self, classifier):
        profile = classifier.classify("What is TOGAF?")
        assert profile.complexity == Complexity.LOW

    def test_complex_architecture_query_is_high_complexity(self, classifier):
        profile = classifier.classify(
            "Design an enterprise architecture for a bank migrating to multi-cloud."
        )
        assert profile.complexity == Complexity.HIGH

    def test_medium_complexity_question(self, classifier):
        profile = classifier.classify(
            "Compare the termination conditions across our vendor contracts."
        )
        assert profile.complexity in (Complexity.MEDIUM, Complexity.HIGH)

    # ── Domain ───────────────────────────────────────────────────────────────

    def test_finance_domain_detected(self, classifier):
        profile = classifier.classify("What is the total revenue and profit forecast?")
        assert profile.domain == Domain.FINANCE

    def test_healthcare_domain_detected(self, classifier):
        profile = classifier.classify(
            "What are the patient diagnosis and treatment protocols?"
        )
        assert profile.domain == Domain.HEALTHCARE

    def test_legal_domain_detected(self, classifier):
        profile = classifier.classify(
            "What are the termination and liability clauses in the contract?"
        )
        assert profile.domain == Domain.LEGAL

    def test_coding_domain_detected(self, classifier):
        profile = classifier.classify("How do I debug this Python function and fix the API bug?")
        assert profile.domain == Domain.CODING

    def test_enterprise_domain_detected(self, classifier):
        profile = classifier.classify(
            "Design a cloud migration strategy and governance framework for our enterprise."
        )
        assert profile.domain == Domain.ENTERPRISE

    def test_general_domain_for_unmatched_query(self, classifier):
        profile = classifier.classify("What is the capital of France?")
        assert profile.domain == Domain.GENERAL

    # ── Sensitivity ──────────────────────────────────────────────────────────

    def test_confidential_sensitivity_detected(self, classifier):
        profile = classifier.classify(
            "What is the CEO's salary and our acquisition plans?"
        )
        assert profile.sensitivity == Sensitivity.CONFIDENTIAL

    def test_internal_sensitivity_detected(self, classifier):
        profile = classifier.classify("Who is our CIO and what is the internal roadmap?")
        assert profile.sensitivity == Sensitivity.INTERNAL

    def test_public_sensitivity_for_generic_query(self, classifier):
        profile = classifier.classify("What is TCP/IP?")
        assert profile.sensitivity == Sensitivity.PUBLIC

    # ── RAG needed ──────────────────────────────────────────────────────────

    def test_rag_needed_for_enterprise_specific_query(self, classifier):
        profile = classifier.classify("Who is our CIO according to our org chart?")
        assert profile.rag_needed is True

    def test_rag_not_needed_for_general_knowledge(self, classifier):
        profile = classifier.classify("Explain how TCP/IP works.")
        assert profile.rag_needed is False

    # ── Latency tier ───────────────────────────────────────────────────────

    def test_batch_latency_for_report_request(self, classifier):
        profile = classifier.classify("Generate a comprehensive analysis report.")
        assert profile.latency_tier == LatencyTier.BATCH

    def test_interactive_latency_for_quick_question(self, classifier):
        profile = classifier.classify("What is TOGAF?")
        assert profile.latency_tier == LatencyTier.INTERACTIVE

    # ── Context size ─────────────────────────────────────────────────────────

    def test_small_context_for_short_query(self, classifier):
        profile = classifier.classify("What is TOGAF?")
        assert profile.context_size == ContextSize.SMALL

    def test_large_context_with_retrieved_context(self, classifier):
        profile = classifier.classify("Summarize this.", context_chars=3000)
        assert profile.context_size == ContextSize.LARGE

    # ── Confidence & tokens ─────────────────────────────────────────────────

    def test_confidence_in_valid_range(self, classifier):
        profile = classifier.classify("Design a multi-cloud architecture for our bank.")
        assert 0.0 <= profile.confidence <= 0.95

    def test_token_estimate_positive(self, classifier):
        profile = classifier.classify("What is TOGAF?")
        assert profile.token_estimate > 0

    def test_signals_populated(self, classifier):
        profile = classifier.classify(
            "Design a multi-cloud architecture for our bank's financial systems."
        )
        assert len(profile.signals) > 0

    # ── Token estimate helper ───────────────────────────────────────────────

    def test_estimate_tokens_short_text(self):
        assert estimate_tokens("hello") >= 1

    def test_estimate_tokens_long_text(self):
        long_text = "word " * 100
        assert estimate_tokens(long_text) > 100

    # ── Integration: full profile ───────────────────────────────────────────

    def test_complex_enterprise_query_full_profile(self, classifier):
        """A complex, confidential, enterprise-domain query should produce
        a profile that the Decision Engine would route to a premium model."""
        profile = classifier.classify(
            "Design a comprehensive enterprise architecture for our bank's "
            "multi-cloud migration, including financial governance and "
            "compliance with our internal policies."
        )
        assert profile.complexity == Complexity.HIGH
        assert profile.domain in (Domain.ENTERPRISE, Domain.FINANCE)
        assert profile.sensitivity in (Sensitivity.INTERNAL, Sensitivity.CONFIDENTIAL)
        assert profile.rag_needed is True
        assert profile.confidence > 0.5
