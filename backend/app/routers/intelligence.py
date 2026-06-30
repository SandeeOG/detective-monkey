"""Student Intelligence Profile endpoints.

Exposes the canonical profile (the single source of truth for understanding a
student) and lightweight engine analytics. All logic lives in the intelligence
service — this router only handles HTTP.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import (
    ConstructScore,
    DomainScore,
    ReliabilityMetric,
    StudentIntelligenceProfile,
    User,
)
from ..student_intelligence import service as intelligence

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


@router.get("/profile")
def my_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = intelligence.get_profile(db, user.id)
    if not profile:
        raise HTTPException(404, "No intelligence profile yet — complete the assessment first")
    return intelligence.serialize(profile)


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Aggregate engine metrics across all stored profiles (research/optimization)."""
    total = db.query(StudentIntelligenceProfile).count()

    avg_constructs = dict(
        db.query(ConstructScore.construct, func.avg(ConstructScore.score))
        .group_by(ConstructScore.construct).all()
    )
    avg_domains = dict(
        db.query(DomainScore.domain, func.avg(DomainScore.score))
        .group_by(DomainScore.domain).all()
    )
    avg_reliability = db.query(func.avg(ReliabilityMetric.reliability_score)).scalar()
    avg_completion = db.query(func.avg(ReliabilityMetric.completion_rate)).scalar()
    avg_exec = db.query(func.avg(StudentIntelligenceProfile.execution_ms)).scalar()

    confidence_dist = dict(
        db.query(ReliabilityMetric.confidence_level, func.count())
        .group_by(ReliabilityMetric.confidence_level).all()
    )

    return {
        "profiles": total,
        "avg_construct_scores": {k: round(v, 4) for k, v in avg_constructs.items()},
        "avg_domain_scores": {k: round(v, 4) for k, v in avg_domains.items()},
        "avg_reliability_score": round(avg_reliability, 2) if avg_reliability is not None else None,
        "avg_completion_rate": round(avg_completion, 4) if avg_completion is not None else None,
        "avg_engine_execution_ms": round(avg_exec, 3) if avg_exec is not None else None,
        "confidence_distribution": confidence_dist,
    }
