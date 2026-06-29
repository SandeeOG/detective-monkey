"""LLM provider factory.

Selects and constructs a provider from environment variables:

    LLM_PROVIDER   provider id: anthropic | gemini | fallback (default: fallback)
    LLM_API_KEY    API key for the selected provider
    LLM_MODEL      model id override (provider has a sensible default)

The offline :class:`FallbackProvider` is returned whenever no provider is
configured, an unknown provider is requested, or a required API key is missing.
Configured cloud providers are wrapped so that any runtime error degrades
gracefully to the fallback instead of failing the request.

Adding a new provider is a one-liner: implement :class:`LLMProvider` and add it
to ``PROVIDERS`` below.
"""
from __future__ import annotations

import os

from .base import ChatRequest, LLMProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.fallback import FallbackProvider
from .providers.gemini_provider import GeminiProvider

# Registry of available providers. Aliases are welcome (e.g. "google" -> Gemini).
PROVIDERS: dict[str, type[LLMProvider]] = {
    "anthropic": AnthropicProvider,
    "claude": AnthropicProvider,
    "gemini": GeminiProvider,
    "google": GeminiProvider,
    "fallback": FallbackProvider,
    "none": FallbackProvider,
}


class _DegradingProvider(LLMProvider):
    """Decorator: delegate to ``inner``; on any error fall back gracefully.

    Preserves the original behaviour of appending an "AI service unavailable"
    note when a configured provider cannot answer.
    """
    requires_api_key = False

    def __init__(self, inner: LLMProvider, fallback: LLMProvider):
        super().__init__()
        self.name = inner.name
        self._inner = inner
        self._fallback = fallback

    def generate(self, request: ChatRequest) -> str:
        try:
            return self._inner.generate(request)
        except Exception as e:  # noqa: BLE001 — any SDK/transport error degrades
            note = (f"\n\n_(AI service unavailable: {type(e).__name__}; "
                    "showing built-in guidance.)_")
            return self._fallback.generate(request) + note


def get_llm() -> LLMProvider:
    """Return the active LLM provider based on the current environment."""
    provider_id = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = os.getenv("LLM_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip()

    cls = PROVIDERS.get(provider_id) if provider_id else None
    # No provider, unknown provider, or explicitly the fallback -> offline mode.
    if cls is None or cls is FallbackProvider:
        return FallbackProvider()

    # A cloud provider that needs a key but has none -> offline mode.
    if cls.requires_api_key and not api_key:
        return FallbackProvider()

    return _DegradingProvider(cls(api_key=api_key, model=model), FallbackProvider())
