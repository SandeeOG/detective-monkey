"""AI Career Coach (PRD section 12).

Builds grounded, student-specific context and delegates generation to the
provider-agnostic LLM layer (:mod:`app.llm`). The active provider — Anthropic,
Gemini, an offline fallback, or any future backend — is chosen by environment
variables; this module is unaware of any concrete SDK.

The coach is an *explanation* layer: it never invents assessment scores or
recommendation rankings — those are passed in as grounded context.
"""
from .llm import ChatRequest, get_llm
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


def generate_reply(message: str, profile, vector: dict | None,
                   recommendations: list[dict], history: list[dict]) -> str:
    request = ChatRequest(
        system=SYSTEM_PROMPT,
        message=message,
        context=build_context(profile, vector, recommendations),
        history=history,
        recommendations=recommendations,
    )
    return get_llm().generate(request)
