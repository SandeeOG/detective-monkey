"""Offline fallback provider.

A deterministic, context-aware explainer used when no LLM provider is
configured (or as graceful degradation when a configured provider errors).
It keeps the AI Coach fully functional with zero external dependencies.
"""
from __future__ import annotations

from ..base import ChatRequest, LLMProvider


class FallbackProvider(LLMProvider):
    name = "fallback"
    requires_api_key = False

    def generate(self, request: ChatRequest) -> str:
        return self._respond(request.message, request.context, request.recommendations)

    @staticmethod
    def _respond(message: str, context: str, recommendations: list[dict]) -> str:
        msg = message.lower()
        rec_names = [r["name"] for r in recommendations]

        if not recommendations and any(w in msg for w in ("recommend", "suit", "career for me", "what career")):
            return ("I'd love to help you find careers that suit you! First, complete the "
                    "assessment so I can understand your interests and strengths. Once that's "
                    "done, I'll be able to explain personalised matches.\n\n"
                    "Next step: head to the Assessment page and answer the questions honestly.")

        if recommendations and any(w in msg for w in ("recommend", "explain", "why", "result")):
            top = recommendations[0]
            others = ", ".join(rec_names[1:4])
            return (f"Based on your assessment, your strongest match is **{top['name']}** "
                    f"({top['score']}% match). {top.get('explanation', '')}\n\n"
                    f"Other careers worth exploring: {others}.\n\n"
                    "Remember these are options to explore, not fixed predictions. "
                    "Next step: open the career details to see the skills and education pathway.")

        if "compare" in msg and len(rec_names) >= 2:
            a, b = recommendations[0], recommendations[1]
            return (f"Comparing your top matches:\n\n"
                    f"- **{a['name']}** — {a['score']}% match. {a.get('explanation','')}\n"
                    f"- **{b['name']}** — {b['score']}% match. {b.get('explanation','')}\n\n"
                    "Both fit your profile well. Think about which day-to-day work excites you more. "
                    "Next step: read both career detail pages and note which responsibilities appeal to you.")

        if any(w in msg for w in ("learn", "skill", "next", "improve", "study")):
            gaps = recommendations[0].get("skill_gaps", []) if recommendations else []
            if gaps:
                return (f"To move toward {recommendations[0]['name']}, focus on developing: "
                        f"{', '.join(gaps)}. Small consistent steps matter most.\n\n"
                        "Next step: pick one of these areas and find a beginner course or school "
                        "project to practise it this month.")
            return ("Great mindset! Keep building strong fundamentals in your favourite subjects, "
                    "and try small projects related to careers that interest you.\n\n"
                    "Next step: complete the assessment so I can suggest targeted skills.")

        # Generic helpful default.
        intro = "I'm your career coach. "
        if recommendations:
            intro += f"Your current top match is {rec_names[0]} ({recommendations[0]['score']}%). "
        return (intro + "You can ask me to explain your recommendations, compare two careers, "
                "or suggest what to learn next. How can I help?\n\n"
                "Next step: try asking 'Explain my recommendations'.")
