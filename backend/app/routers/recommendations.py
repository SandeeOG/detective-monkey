"""Recommendation engine endpoints (FR-004 / PRD section 11)."""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Career, Recommendation, User
from ..recommender import generate_recommendations
from ..student_intelligence import service as intelligence

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def _serialize(rec: Recommendation) -> dict:
    return {
        "rank": rec.rank,
        "score": rec.score,
        "confidence": rec.confidence,
        "explanation": rec.explanation,
        "matched_constructs": rec.matched_constructs or [],
        "career": {
            "slug": rec.career.slug,
            "name": rec.career.name,
            "category": rec.career.category,
            "description": rec.career.description,
            "salary_range": rec.career.salary_range,
            "outlook": rec.career.outlook,
        },
    }


@router.post("/generate")
def generate(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Consume the Student Intelligence Profile — never reprocess raw responses.
    profile = intelligence.get_profile(db, user.id)
    if not profile:
        raise HTTPException(400, "Complete the assessment before generating recommendations")

    vector = intelligence.construct_vector(profile)
    answered_ratio = intelligence.completion_rate(profile)

    careers = db.query(Career).all()
    results = generate_recommendations(vector, careers, answered_ratio, top_n=5)

    # Replace the previous batch for this user.
    db.query(Recommendation).filter(Recommendation.user_id == user.id).delete()
    batch_id = uuid.uuid4().hex
    stored = []
    for r in results:
        rec = Recommendation(
            user_id=user.id, batch_id=batch_id, career_id=r["career"].id,
            score=r["score"], confidence=r["confidence"], rank=r["rank"],
            explanation=r["explanation"], matched_constructs=r["matched_constructs"],
        )
        db.add(rec)
        stored.append(rec)
    db.commit()
    for rec in stored:
        db.refresh(rec)
    return {"batch_id": batch_id, "recommendations": [_serialize(r) for r in stored]}


@router.get("")
def list_recommendations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.rank)
        .all()
    )
    return {"recommendations": [_serialize(r) for r in recs]}
