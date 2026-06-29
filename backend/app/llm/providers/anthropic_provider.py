"""Anthropic (Claude) provider."""
from __future__ import annotations

from ..base import ChatRequest, LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    requires_api_key = True
    default_model = "claude-sonnet-4-6"

    def generate(self, request: ChatRequest) -> str:
        import anthropic  # lazy import keeps the SDK optional

        client = anthropic.Anthropic(api_key=self.api_key)
        messages = [{"role": h["role"], "content": h["content"]} for h in request.history[-8:]]
        messages.append({"role": "user", "content": request.user_turn()})

        resp = client.messages.create(
            model=self.model,
            max_tokens=request.max_tokens,
            system=request.system,
            messages=messages,
        )
        return "".join(block.text for block in resp.content if block.type == "text").strip()
