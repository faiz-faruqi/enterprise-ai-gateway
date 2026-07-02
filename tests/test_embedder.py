"""
Unit tests for the Embedder class.

These tests load the real SentenceTransformer model (all-MiniLM-L6-v2).
The model is small (~22MB) and loads quickly, making this acceptable in CI.
Results are validated by shape and mathematical properties, not exact values.
"""

import math

import pytest

from src.retrieval.embedder import Embedder


@pytest.fixture(scope="module")
def embedder():
    """Shared embedder instance across all tests in this module."""
    return Embedder()


class TestEmbedder:
    def test_embed_single_returns_list(self, embedder):
        result = embedder.embed_single("What are the termination conditions?")
        assert isinstance(result, list)

    def test_embed_single_has_correct_dimension(self, embedder):
        result = embedder.embed_single("Test text")
        assert len(result) == 384

    def test_embed_single_contains_floats(self, embedder):
        result = embedder.embed_single("Test text")
        assert all(isinstance(v, float) for v in result)

    def test_embed_single_is_normalized(self, embedder):
        """Embeddings should have unit magnitude (L2 norm ≈ 1.0)."""
        result = embedder.embed_single("Normalized embedding test")
        magnitude = math.sqrt(sum(v * v for v in result))
        assert abs(magnitude - 1.0) < 1e-4

    def test_embed_batch_returns_correct_count(self, embedder):
        texts = [
            "Contract termination clause",
            "Data protection obligations",
            "Payment schedule and milestones",
        ]
        results = embedder.embed(texts)
        assert len(results) == 3

    def test_embed_batch_each_has_correct_dimension(self, embedder):
        texts = ["First document.", "Second document."]
        results = embedder.embed(texts)
        for vec in results:
            assert len(vec) == 384

    def test_embed_single_string_equals_batch_of_one(self, embedder):
        text = "Liability cap and indemnification"
        single = embedder.embed_single(text)
        batch = embedder.embed(text)  # string input to embed()
        assert len(batch) == 1
        # Values should be identical
        assert all(abs(a - b) < 1e-6 for a, b in zip(single, batch[0]))

    def test_similar_texts_have_higher_cosine_similarity(self, embedder):
        """Semantically similar texts should score higher than dissimilar ones."""
        base = embedder.embed_single("Contract termination with 90 days notice")
        similar = embedder.embed_single("Agreement can be ended with 90 day written notice")
        different = embedder.embed_single("Quarterly financial reporting obligations")

        def cosine(a: list[float], b: list[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            mag_a = math.sqrt(sum(x * x for x in a))
            mag_b = math.sqrt(sum(x * x for x in b))
            return dot / (mag_a * mag_b)

        sim_similar = cosine(base, similar)
        sim_different = cosine(base, different)
        assert sim_similar > sim_different
