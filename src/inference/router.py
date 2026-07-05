"""
Inference Router — primary/fallback provider selection.

Design decision: local-first. Cloud is used only when:
  1. The caller explicitly requests it (force_cloud=True), or
  2. The local Ollama node is unreachable or returns an error.

This implements ADR 0001 (Local-First Hybrid Inference Strategy).

Phase 1 extension: the router now also supports explicit model selection
via a model alias. When `model` is provided, the router looks up the
provider in the ProviderRegistry and calls it directly (with the existing
local→cloud fallback still applying if that provider is a local model
that fails). When `model` is None, the legacy local-first behaviour is
preserved unchanged — this keeps the existing query endpoint and tests
working without modification.
"""

import logging
import os
from enum import Enum

from src.inference.base_provider import Provider
from src.inference.ollama_client import OllamaClient
from src.inference.openrouter_client import OpenRouterClient
from src.inference.provider_registry import ProviderRegistry

logger = logging.getLogger(__name__)

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


class ProviderResult(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class InferenceRouter:
    """
    Routes inference requests between local (Ollama) and cloud (OpenRouter).

    The router does not know about caching — cache lookup is handled
    upstream in the query endpoint before reaching this layer.
    """

    def __init__(
        self,
        ollama: OllamaClient,
        openrouter: OpenRouterClient,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self._ollama = ollama
        self._openrouter = openrouter
        self._registry = registry

    # ── Legacy local-first path (unchanged) ──────────────────────────────────
    async def complete(
        self,
        prompt: str,
        force_cloud: bool = False,
    ) -> tuple[str, ProviderResult]:
        """
        Generate a completion for the given grounded prompt.

        Returns:
            A tuple of (response_text, provider_used).
        """
        if not force_cloud and not DEMO_MODE:
            try:
                logger.info("Routing to local inference (Ollama).")
                response = await self._ollama.complete(prompt)
                return response, ProviderResult.LOCAL
            except Exception as exc:
                logger.warning(
                    "Local inference failed — falling back to cloud. Reason: %s",
                    exc,
                )

        logger.info("Routing to cloud inference (OpenRouter).")
        response = await self._openrouter.complete(prompt)
        return response, ProviderResult.CLOUD

    # ── Phase 1: explicit model selection via registry ───────────────────────
    async def complete_with_model(
        self,
        prompt: str,
        model_alias: str,
    ) -> tuple[str, ProviderResult, str]:
        """
        Generate a completion using a specific model from the registry.

        For local models, the standard local→cloud fallback still applies
        if the local node is unavailable. For cloud models, the chosen
        provider is called directly.

        Returns:
            A tuple of (response_text, provider_used, model_alias_used).
        """
        if self._registry is None:
            raise RuntimeError("ProviderRegistry not configured for this router.")

        provider = self._registry.get(model_alias)
        if provider is None:
            raise ValueError(f"Unknown model alias: '{model_alias}'.")

        # Local models retain graceful fallback to cloud on failure.
        if provider.is_local and not DEMO_MODE:
            try:
                logger.info("Routing to explicit local model: %s", model_alias)
                response = await provider.complete(prompt)
                return response, ProviderResult.LOCAL, model_alias
            except Exception as exc:
                logger.warning(
                    "Local model '%s' failed — falling back to cloud. Reason: %s",
                    model_alias, exc,
                )
                response = await self._openrouter.complete(prompt)
                return response, ProviderResult.CLOUD, model_alias

        # Cloud model (or DEMO_MODE) — call directly.
        logger.info("Routing to explicit cloud model: %s", model_alias)
        if provider.is_local and DEMO_MODE:
            response = await self._openrouter.complete(prompt)
        else:
            response = await provider.complete(prompt)
        return response, ProviderResult.CLOUD, model_alias
