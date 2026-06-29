"""Google Gemini provider (Google GenAI SDK).

Uses the ``google-genai`` package: https://pypi.org/project/google-genai/
"""
from __future__ import annotations

from ..base import ChatRequest, LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"
    requires_api_key = True
    default_model = "gemini-2.0-flash"

    def generate(self, request: ChatRequest) -> str:
        from google import genai  # lazy import keeps the SDK optional
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        # Gemini uses the role name "model" for assistant turns.
        contents = []
        for h in request.history[-8:]:
            role = "model" if h["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": h["content"]}]})
        contents.append({"role": "user", "parts": [{"text": request.user_turn()}]})

        resp = client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=request.system,
                max_output_tokens=request.max_tokens,
            ),
        )
        return (resp.text or "").strip()
