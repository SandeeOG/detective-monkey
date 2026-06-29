"""AI Career Coach (PRD section 12).

Builds student-specific context and produces a response. If an Anthropic API
key is configured the response comes from Claude; otherwise a deterministic,
context-aware fallback keeps the feature fully functional offline.

The coach is an *explanation* layer: it never invents assessment scores or
recommendation rankings — those are passed in as grounded context.
"""
from .config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
from .seed_data import CONSTRUCT_LABELS

SYSTEM_PROMPT = (
    "You are Detective Monkey, a warm, encouraging AI career coach for students "
    "in grades 8-12. You explain assessment results and career recommendations in "
    "clear, simple language. Rules: (1) Use ONLY the student context provided — never "
    "invent scores, rankings or facts. (2) Always frame guidance as supportive options, "
    "never guarantees about the future. (3) Encourage the student to also talk to "
    "parents, teachers and counsellors. (4) Do not give legal, financial or medical "
    "advice. (5) Keep answers concise and actionable, ending with a suggested next step."
)


def build_context(profile, vector: dict | None, recommendations: list[dict]) -> str:
    lines = []
    if profile:
        lines.append("STUDENT PROFILE:")
        lines.append(f"- Name: {profile.get('full_name', 'Student')}")
        if profile.get("grade"):
            lines.append(f"- Grade: {profile['grade']}")
        if profile.get("favourite_subjects"):
            lines.append(f"- Favourite subjects: {', '.join(profile['favourite_subjects'])}")
        if profile.get("career_aspiration"):
            lines.append(f"- Career aspiration: {profile['career_aspiration']}")

    if vector:
        top = sorted(vector.items(), key=lambda kv: kv[1], reverse=True)[:6]
        lines.append("\nTOP STRENGTHS (from assessment, 0-1 scale):")
        for c, v in top:
            lines.append(f"- {CONSTRUCT_LABELS.get(c, c)}: {v:.2f}")
    else:
        lines.append("\nThe student has not completed the assessment yet.")

    if recommendations:
        lines.append("\nCAREER RECOMMENDATIONS (already generated for this student):")
        for r in recommendations:
            lines.append(f"- {r['name']} — match {r['score']}% ({r['confidence']} confidence)")
    return "\n".join(lines)


def _fallback_response(message: str, context: str, recommendations: list[dict]) -> str:
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


def generate_reply(message: str, profile, vector: dict | None,
                   recommendations: list[dict], history: list[dict]) -> str:
    context = build_context(profile, vector, recommendations)

    if ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            messages = []
            for h in history[-8:]:
                messages.append({"role": h["role"], "content": h["content"]})
            messages.append({
                "role": "user",
                "content": f"Student context:\n{context}\n\nStudent question: {message}",
            })
            resp = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=messages,
            )
            return "".join(block.text for block in resp.content if block.type == "text").strip()
        except Exception as e:  # noqa: BLE001 — gracefully degrade to fallback
            return (_fallback_response(message, context, recommendations)
                    + f"\n\n_(AI service unavailable: {type(e).__name__}; showing built-in guidance.)_")

    return _fallback_response(message, context, recommendations)
