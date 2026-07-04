"""Provider implementations wrapping existing inference clients."""

from src.inference.providers.ollama_provider import OllamaProvider
from src.inference.providers.openrouter_provider import OpenRouterProvider

__all__ = ["OllamaProvider", "OpenRouterProvider"]
