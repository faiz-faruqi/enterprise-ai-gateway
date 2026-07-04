"""
Tests for the Phase 1 provider abstraction and registry.

Verifies:
  - The model catalog is non-empty and well-formed.
  - The registry builds a Provider for every catalog entry.
  - Provider type selection (local vs cloud) matches is_local.
  - by_tier filtering works.
  - Explicit model selection routes to the right provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.models import MODEL_CATALOG, ModelDefinition, get_model, list_models
from src.inference.base_provider import Provider
from src.inference.provider_registry import ProviderRegistry
from src.inference.providers.ollama_provider import OllamaProvider
from src.inference.providers.openrouter_provider import OpenRouterProvider
from src.inference.router import InferenceRouter, ProviderResult


# ── Model catalog ────────────────────────────────────────────────────────────


class TestModelCatalog:
    def test_catalog_has_entries(self):
        assert len(MODEL_CATALOG) >= 6, "Catalog should have multiple models."

    def test_every_entry_has_required_fields(self):
        for alias, model in MODEL_CATALOG.items():
            assert model.alias == alias
            assert model.vendor
            assert model.model_id
            assert model.tier in {"local", "cheap", "standard", "premium"}
            assert model.context_window > 0
            assert model.cost_per_1k_input >= 0.0
            assert model.cost_per_1k_output >= 0.0
            assert model.latency_tier in {"fast", "balanced", "slow"}
            assert isinstance(model.is_local, bool)

    def test_local_models_have_zero_cost(self):
        for model in MODEL_CATALOG.values():
            if model.is_local:
                assert model.cost_per_1k_input == 0.0
                assert model.cost_per_1k_output == 0.0

    def test_get_model_returns_definition(self):
        model = get_model("gpt-4o")
        assert model is not None
        assert model.vendor == "openai"

    def test_get_unknown_model_returns_none(self):
        assert get_model("nonexistent-model") is None

    def test_list_models_returns_all(self):
        models = list_models()
        assert len(models) == len(MODEL_CATALOG)

    def test_all_tiers_represented(self):
        tiers = {m.tier for m in MODEL_CATALOG.values()}
        assert "local" in tiers
        assert "cheap" in tiers
        assert "standard" in tiers
        assert "premium" in tiers


# ── Provider Registry ────────────────────────────────────────────────────────


class TestProviderRegistry:
    @pytest.fixture
    def registry(self):
        # Patch the underlying clients so no real network calls happen on build.
        with patch(
            "src.inference.providers.ollama_provider.OllamaClient"
        ), patch(
            "src.inference.providers.openrouter_provider.OpenRouterClient"
        ):
            return ProviderRegistry()

    def test_builds_provider_for_every_catalog_entry(self, registry):
        assert len(registry.all()) == len(MODEL_CATALOG)

    def test_all_entries_are_providers(self, registry):
        for provider in registry.all():
            assert isinstance(provider, Provider)

    def test_local_models_become_ollama_providers(self, registry):
        for provider in registry.local_providers():
            assert isinstance(provider, OllamaProvider)
            assert provider.is_local is True

    def test_cloud_models_become_openrouter_providers(self, registry):
        for provider in registry.cloud_providers():
            assert isinstance(provider, OpenRouterProvider)
            assert provider.is_local is False

    def test_get_returns_provider(self, registry):
        provider = registry.get("gpt-4o")
        assert provider is not None
        assert provider.alias == "gpt-4o"

    def test_get_unknown_returns_none(self, registry):
        assert registry.get("nope") is None

    def test_by_tier(self, registry):
        premium = registry.by_tier("premium")
        assert len(premium) >= 1
        for p in premium:
            assert p.info.tier == "premium"

    def test_aliases(self, registry):
        aliases = registry.aliases()
        assert "gpt-4o" in aliases
        assert "local-gemma" in aliases

    def test_describe_is_json_serialisable(self, registry):
        import json
        description = registry.describe()
        # Must not raise.
        json.dumps(description)
        assert len(description) == len(MODEL_CATALOG)
        first = description[0]
        assert "alias" in first
        assert "cost_per_1k_input" in first


# ── Explicit model selection via router ─────────────────────────────────────


class TestExplicitModelSelection:
    @pytest.fixture
    def registry_with_mocks(self):
        """Build a registry where every provider's complete() is mocked."""
        with patch(
            "src.inference.providers.ollama_provider.OllamaClient"
        ), patch(
            "src.inference.providers.openrouter_provider.OpenRouterClient"
        ):
            reg = ProviderRegistry()
            # Replace complete() on every provider with an AsyncMock.
            for provider in reg.all():
                provider.complete = AsyncMock(
                    return_value=f"Mocked answer from {provider.alias}."
                )
            return reg

    @pytest.fixture
    def router(self, registry_with_mocks, mock_ollama, mock_openrouter):
        return InferenceRouter(
            ollama=mock_ollama,
            openrouter=mock_openrouter,
            registry=registry_with_mocks,
        )

    async def test_cloud_model_called_directly(self, router, registry_with_mocks):
        answer, provider, alias = await router.complete_with_model(
            "prompt", "gpt-4o"
        )
        assert alias == "gpt-4o"
        assert provider == ProviderResult.CLOUD
        assert "gpt-4o" in answer
        gpt_provider = registry_with_mocks.get("gpt-4o")
        gpt_provider.complete.assert_called_once_with("prompt")

    async def test_unknown_model_raises(self, router):
        with pytest.raises(ValueError, match="Unknown model alias"):
            await router.complete_with_model("prompt", "does-not-exist")

    async def test_router_without_registry_raises(self, mock_ollama, mock_openrouter):
        bare_router = InferenceRouter(
            ollama=mock_ollama, openrouter=mock_openrouter, registry=None
        )
        with pytest.raises(RuntimeError, match="ProviderRegistry not configured"):
            await bare_router.complete_with_model("prompt", "gpt-4o")

    async def test_legacy_complete_still_works(self, router, mock_ollama):
        """The original complete() path must remain unaffected."""
        answer, provider = await router.complete("prompt")
        assert provider == ProviderResult.LOCAL
        assert answer == "Local model answer from Ollama."
