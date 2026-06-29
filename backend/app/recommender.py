"""Rules-based recommendation engine (PRD section 11).

Compares a Student Feature Vector against each career's ideal profile using a
weighted similarity, producing a 0..100 compatibility score, a confidence
band, a transparent explanation and skill-gap hints.
"""
from .seed_data import CONSTRUCT_LABELS


def _career_score(vector: dict[str, float], weights: dict[str, float]) -> tuple[float, list[dict]]:
    """Weighted similarity between student vector and a career's ideal profile.

    For each construct the career cares about, closeness = 1 - |student - ideal|,
    weighted by how important that construct is to the career. The result is the
    weighted-average closeness, scaled to 0..100.
    """
    total_w = 0.0
    acc = 0.0
    contributions = []
    for construct, ideal in weights.items():
        student = vector.get(construct, 0.5)
        closeness = 1.0 - abs(student - ideal)
        w = ideal  # importance ~ how strongly the career demands this trait
        acc += closeness * w
        total_w += w
        contributions.append({
            "construct": construct,
            "label": CONSTRUCT_LABELS.get(construct, construct),
            "student": round(student, 2),
            "ideal": round(ideal, 2),
            "closeness": round(closeness, 3),
            "importance": round(w, 2),
        })
    score = (acc / total_w) * 100 if total_w else 0.0
    contributions.sort(key=lambda c: (c["importance"], c["closeness"]), reverse=True)
    return round(score, 1), contributions


def _confidence(score: float, answered_ratio: float) -> str:
    if answered_ratio < 0.6:
        return "Low"
    if score >= 78:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def _explain(career_name: str, contributions: list[dict]) -> tuple[str, list[str]]:
    """Build a plain-language explanation and the list of matched constructs."""
    strong = [c for c in contributions if c["closeness"] >= 0.8 and c["importance"] >= 0.6]
    strong = strong[:3] or contributions[:2]
    matched = [c["label"] for c in strong]
    if matched:
        traits = ", ".join(matched[:-1]) + (f" and {matched[-1]}" if len(matched) > 1 else matched[0]) \
            if len(matched) > 1 else matched[0]
        text = (f"You scored well on {traits}, which are central to succeeding as a "
                f"{career_name}. That alignment makes this a strong match worth exploring.")
    else:
        text = f"Your profile shows a reasonable fit with {career_name}."
    return text, matched


def _skill_gaps(contributions: list[dict]) -> list[str]:
    """Constructs the career values but where the student is below the ideal."""
    gaps = [c for c in contributions if c["importance"] >= 0.6 and c["student"] < c["ideal"] - 0.15]
    gaps.sort(key=lambda c: (c["ideal"] - c["student"]), reverse=True)
    return [c["label"] for c in gaps[:3]]


def generate_recommendations(vector: dict[str, float], careers, answered_ratio: float, top_n: int = 5):
    """Score every career and return the top N ranked recommendations."""
    scored = []
    for career in careers:
        weights = career.profile_weights or {}
        if not weights:
            continue
        score, contributions = _career_score(vector, weights)
        explanation, matched = _explain(career.name, contributions)
        scored.append({
            "career": career,
            "score": score,
            "confidence": _confidence(score, answered_ratio),
            "explanation": explanation,
            "matched_constructs": matched,
            "skill_gaps": _skill_gaps(contributions),
            "contributions": contributions,
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    for i, r in enumerate(scored[:top_n], start=1):
        r["rank"] = i
    return scored[:top_n]
