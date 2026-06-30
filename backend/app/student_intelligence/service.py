"""Student Intelligence Service.

The only place that couples the pure engine to the database. Routers call this
service; they never contain intelligence logic. Responsibilities:

    Load assessment questions -> run engine -> persist normalized profile
    -> provide retrieval & serialization for downstream consumers.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import (
    ConstructScore,
    DerivedFeature,
    DomainScore,
    Question,
    ReliabilityMetric,
    StudentIntelligenceProfile,
)
from . import config, engine
from .types import IntelligenceProfile, QuestionMeta


def _load_question_meta(db: Session) -> dict[int, QuestionMeta]:
    questions = db.query(Question).all()
    return {
        q.id: QuestionMeta(
            id=q.id, construct=q.construct, domain=q.domain,
            weight=q.weight or 1.0, reverse=bool(q.reverse),
        )
        for q in questions
    }


def generate_profile(
    db: Session, user_id: int, session_id: int | None,
    responses: list[tuple[int, float]],
) -> StudentIntelligenceProfile:
    """Run the engine and persist the resulting profile (one current per user)."""
    questions = _load_question_meta(db)
    profile = engine.run(responses, questions, student_id=user_id, session_id=session_id)
    return _persist(db, user_id, session_id, profile)


def _persist(
    db: Session, user_id: int, session_id: int | None, profile: IntelligenceProfile,
) -> StudentIntelligenceProfile:
    # Replace any existing profile for this user (cascade removes children).
    existing = (
        db.query(StudentIntelligenceProfile)
        .filter(StudentIntelligenceProfile.user_id == user_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.flush()

    row = StudentIntelligenceProfile(
        user_id=user_id, session_id=session_id,
        engine_version=profile.metadata["engine_version"],
        scoring_version=profile.metadata["scoring_version"],
        assessment_version=profile.metadata["assessment_version"],
        execution_ms=profile.metadata.get("execution_ms"),
    )
    for construct, score in profile.construct_scores.items():
        row.construct_scores.append(
            ConstructScore(construct=construct, domain=config.DOMAIN_OF.get(construct, ""), score=score)
        )
    for domain, score in profile.domain_scores.items():
        row.domain_scores.append(DomainScore(domain=domain, score=score))
    for f in profile.derived_features:
        row.derived_features.append(DerivedFeature(
            key=f.key, label=f.label, value=f.value, level=f.level,
            sources=f.sources, explanation=f.explanation,
        ))
    r = profile.reliability
    row.reliability = ReliabilityMetric(
        completion_rate=r.completion_rate, response_consistency=r.response_consistency,
        reliability_score=r.reliability_score, confidence_level=r.confidence_level,
    )
    db.add(row)
    db.flush()
    return row


# --- Retrieval helpers (downstream consumers use these, not the ORM directly) ---
def get_profile(db: Session, user_id: int) -> StudentIntelligenceProfile | None:
    return (
        db.query(StudentIntelligenceProfile)
        .filter(StudentIntelligenceProfile.user_id == user_id)
        .first()
    )


def construct_vector(profile: StudentIntelligenceProfile) -> dict[str, float]:
    """The construct-score dict consumed by the recommendation engine, coach and reports."""
    return profile.vector


def completion_rate(profile: StudentIntelligenceProfile) -> float:
    return profile.reliability.completion_rate if profile.reliability else 0.0


def serialize(profile: StudentIntelligenceProfile) -> dict:
    """Canonical Student Intelligence Profile as a JSON-friendly dict."""
    return {
        "metadata": {
            "student_id": profile.user_id,
            "session_id": profile.session_id,
            "generated_at": profile.generated_at.isoformat() if profile.generated_at else None,
            "engine_version": profile.engine_version,
            "scoring_version": profile.scoring_version,
            "assessment_version": profile.assessment_version,
            "execution_ms": profile.execution_ms,
        },
        "construct_scores": [
            {"construct": cs.construct, "label": config.LABELS.get(cs.construct, cs.construct),
             "domain": cs.domain, "score": cs.score}
            for cs in sorted(profile.construct_scores, key=lambda x: x.score, reverse=True)
        ],
        "domain_scores": [
            {"domain": ds.domain, "score": ds.score} for ds in profile.domain_scores
        ],
        "derived_features": [
            {"key": f.key, "label": f.label, "value": f.value, "level": f.level,
             "sources": f.sources or [], "explanation": f.explanation}
            for f in sorted(profile.derived_features, key=lambda x: x.value, reverse=True)
        ],
        "reliability": {
            "completion_rate": profile.reliability.completion_rate,
            "response_consistency": profile.reliability.response_consistency,
            "reliability_score": profile.reliability.reliability_score,
            "confidence_level": profile.reliability.confidence_level,
        } if profile.reliability else None,
    }
