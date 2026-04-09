"""
Inference Router — primary/fallback provider selection.

Design decision: local-first. Cloud is used only when:
  1. The caller explicitly requests it (force_cloud=True), or
  2. The local Ollama node is unreachable or returns an error.

This implements ADR 0001 (Local-First Hybrid Inference Strategy).
"""

import logging
from enum import Enum

from src.inference.ollama_client import OllamaClient
from src.inference.openrouter_client import OpenRouterClient

logger = logging.getLogger(__name__)


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
    ) -> None:
        self._ollama = ollama
        self._openrouter = openrouter

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
        if not force_cloud:
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
