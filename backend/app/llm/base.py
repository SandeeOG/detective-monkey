"""Provider-agnostic LLM interface.

Every provider (Anthropic, Gemini, the offline fallback, and any future
backend such as OpenAI or Ollama) implements :class:`LLMProvider`. The rest of
the application depends only on this interface and on :class:`ChatRequest` —
never on a concrete SDK.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChatRequest:
    """A single coach turn, expressed in provider-neutral terms.

    Attributes:
        system: System / behaviour prompt.
        message: The student's latest question.
        context: Pre-built, grounded student context (profile, strengths,
            recommendations) injected into the user turn.
        history: Prior turns as ``[{"role": "user"|"assistant", "content": str}]``.
        recommendations: Structured recommendation data. Cloud providers ignore
            this; the offline fallback uses it to craft grounded replies.
        max_tokens: Soft cap on the response length.
    """
    system: str
    message: str
    context: str = ""
    history: list[dict] = field(default_factory=list)
    recommendations: list[dict] = field(default_factory=list)
    max_tokens: int = 600

    def user_turn(self) -> str:
        """The fully-assembled user message (context + question) most cloud
        chat APIs expect as the final user turn."""
        if self.context:
            return f"Student context:\n{self.context}\n\nStudent question: {self.message}"
        return self.message


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    #: Human-readable provider id (used in logs / errors).
    name: str = "base"
    #: Whether a non-empty API key is required for this provider to function.
    requires_api_key: bool = True
    #: Default model used when ``LLM_MODEL`` is not set.
    default_model: str = ""

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key
        self.model = model or self.default_model

    @abstractmethod
    def generate(self, request: ChatRequest) -> str:
        """Return the assistant's reply text for ``request``.

        Implementations may raise on transport/SDK errors; callers obtaining a
        provider from the factory get automatic degradation to the offline
        fallback (see :mod:`app.llm.factory`).
        """
        raise NotImplementedError
