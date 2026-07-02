"""
Unit tests for InferenceRouter.

Tests the local-first routing logic, fallback behaviour, and force_cloud flag.
All LLM clients are mocked — no real HTTP calls are made.
"""

import pytest

from src.inference.router import InferenceRouter, ProviderResult


class TestInferenceRouter:
    @pytest.fixture
    def router(self, mock_ollama, mock_openrouter):
        return InferenceRouter(ollama=mock_ollama, openrouter=mock_openrouter)

    async def test_routes_to_local_by_default(self, router, mock_ollama, mock_openrouter):
        """Default path should use Ollama (local) when available."""
        answer, provider = await router.complete("Test prompt")
        assert provider == ProviderResult.LOCAL
        assert answer == "Local model answer from Ollama."
        mock_ollama.complete.assert_called_once_with("Test prompt")
        mock_openrouter.complete.assert_not_called()

    async def test_falls_back_to_cloud_on_local_failure(self, router, mock_ollama, mock_openrouter):
        """When Ollama raises, router must fall back to OpenRouter."""
        import httpx
        mock_ollama.complete.side_effect = httpx.ConnectError("Ollama unreachable")
        answer, provider = await router.complete("Test prompt")
        assert provider == ProviderResult.CLOUD
        assert answer == "Cloud model answer from OpenRouter."
        mock_ollama.complete.assert_called_once()
        mock_openrouter.complete.assert_called_once()

    async def test_falls_back_on_generic_exception(self, router, mock_ollama, mock_openrouter):
        """Any exception from Ollama should trigger cloud fallback."""
        mock_ollama.complete.side_effect = RuntimeError("Unexpected error")
        answer, provider = await router.complete("Test prompt")
        assert provider == ProviderResult.CLOUD

    async def test_force_cloud_bypasses_local(self, router, mock_ollama, mock_openrouter):
        """force_cloud=True should skip Ollama entirely."""
        answer, provider = await router.complete("Test prompt", force_cloud=True)
        assert provider == ProviderResult.CLOUD
        assert answer == "Cloud model answer from OpenRouter."
        mock_ollama.complete.assert_not_called()
        mock_openrouter.complete.assert_called_once_with("Test prompt")

    async def test_local_answer_is_returned_verbatim(self, router, mock_ollama):
        """The exact response from Ollama should be returned unchanged."""
        mock_ollama.complete.return_value = "Specific contract answer.\n\nWith a second paragraph."
        answer, _ = await router.complete("Some query")
        assert answer == "Specific contract answer.\n\nWith a second paragraph."

    async def test_provider_result_values(self):
        """ProviderResult enum values are stable strings."""
        assert ProviderResult.LOCAL == "local"
        assert ProviderResult.CLOUD == "cloud"
