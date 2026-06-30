"""Career report (FR-007 / PRD section 15).

Aggregates the student's profile, feature vector, recommendations and skill
gaps into a single payload. The frontend renders it as a printable report
(print-to-PDF), satisfying the 'download report' requirement without a
heavyweight PDF dependency.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Profile, Recommendation, User
from ..recommender import _career_score, _skill_gaps
from ..seed_data import CONSTRUCTS, CONSTRUCT_LABELS
from ..student_intelligence import service as intelligence

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("")
def report(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    intel = intelligence.get_profile(db, user.id)
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.rank)
        .all()
    )
    if not intel or not recs:
        raise HTTPException(400, "Complete the assessment and generate recommendations first")

    vector = intelligence.construct_vector(intel)
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    domain_of = {c: d for d, cs in CONSTRUCTS.items() for c in cs}

    strengths = sorted(vector.items(), key=lambda kv: kv[1], reverse=True)[:5]
    strengths_out = [
        {"label": CONSTRUCT_LABELS.get(c, c), "domain": domain_of.get(c, ""), "score": v}
        for c, v in strengths
    ]

    rec_out, all_gaps = [], []
    for r in recs:
        _, contributions = _career_score(vector, r.career.profile_weights or {})
        gaps = _skill_gaps(contributions)
        all_gaps.extend(gaps)
        rec_out.append({
            "rank": r.rank, "name": r.career.name, "category": r.career.category,
            "score": r.score, "confidence": r.confidence, "explanation": r.explanation,
            "skill_gaps": gaps,
            "education_pathway": r.career.education_pathway,
        })

    # De-duplicated, ordered skill gaps -> next steps.
    seen, ordered_gaps = set(), []
    for g in all_gaps:
        if g not in seen:
            seen.add(g)
            ordered_gaps.append(g)

    next_steps = [
        f"Explore the day-to-day work of {rec_out[0]['name']} on its career page.",
        "Talk through these results with a parent, teacher or school counsellor.",
    ]
    for g in ordered_gaps[:3]:
        next_steps.append(f"Build your {g} through a course, club or small project.")
    next_steps.append("Revisit the assessment as your interests evolve to refine your matches.")

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "student": {
            "name": user.full_name,
            "grade": getattr(profile, "grade", None),
            "school": getattr(profile, "school", None),
            "favourite_subjects": getattr(profile, "favourite_subjects", []) or [],
            "career_aspiration": getattr(profile, "career_aspiration", None),
        },
        "strengths": strengths_out,
        "recommendations": rec_out,
        "skill_gaps": ordered_gaps[:5],
        "next_steps": next_steps,
        # --- Student Intelligence Profile enrichment (additive) ---
        "domain_scores": [{"domain": d.domain, "score": d.score} for d in intel.domain_scores],
        "derived_features": [
            {"label": f.label, "level": f.level, "value": f.value}
            for f in sorted(intel.derived_features, key=lambda x: x.value, reverse=True)[:5]
        ],
        "reliability": {
            "reliability_score": intel.reliability.reliability_score,
            "confidence_level": intel.reliability.confidence_level,
            "completion_rate": intel.reliability.completion_rate,
            "response_consistency": intel.reliability.response_consistency,
        } if intel.reliability else None,
        "disclaimer": (
            "This report offers guidance, not a prediction or guarantee. It is a starting "
            "point for conversations with the people who support you."
        ),
    }
