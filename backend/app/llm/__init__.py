"""Provider-agnostic LLM package.

Public surface used by the rest of the app:

    from .llm import get_llm, ChatRequest

    reply = get_llm().generate(ChatRequest(system=..., message=..., ...))
"""
from .base import ChatRequest, LLMProvider
from .factory import PROVIDERS, get_llm

__all__ = ["get_llm", "ChatRequest", "LLMProvider", "PROVIDERS"]
