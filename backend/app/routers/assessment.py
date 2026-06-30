"""Assessment engine endpoints (FR-003 / PRD section 10).

Collects responses and delegates all interpretation to the Student Intelligence
Engine (``app.student_intelligence``). This router contains no scoring logic.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import AssessmentSession, Question, Response, StudentIntelligenceProfile, User
from ..schemas import SubmitIn
from ..student_intelligence import service as intelligence
from ..student_intelligence.config import ALL_CONSTRUCTS, DOMAIN_OF, LABELS

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.get("/questions")
def get_questions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Return the question bank grouped by domain (no scoring metadata leaked)."""
    from ..seed_data import CONSTRUCTS

    questions = db.query(Question).order_by(Question.order_index).all()
    by_domain: dict[str, list] = {domain: [] for domain in CONSTRUCTS}
    for q in questions:
        by_domain.setdefault(q.domain, []).append({
            "id": q.id, "code": q.code, "text": q.text,
            "construct": q.construct, "type": q.qtype,
        })
    groups = [{"domain": d, "questions": qs} for d, qs in by_domain.items() if qs]
    return {"total": len(questions), "groups": groups}


@router.post("/submit")
def submit(payload: SubmitIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not payload.responses:
        raise HTTPException(400, "No responses provided")

    # Persist a completed session with its responses.
    session = AssessmentSession(user_id=user.id, status="completed", completed_at=datetime.utcnow())
    db.add(session)
    db.flush()
    pairs: list[tuple[int, float]] = []
    for r in payload.responses:
        db.add(Response(session_id=session.id, question_id=r.question_id, value=r.value))
        pairs.append((r.question_id, r.value))

    # The intelligence engine produces and stores the canonical profile.
    profile = intelligence.generate_profile(db, user.id, session.id, pairs)
    db.commit()
    return {
        "session_id": session.id,
        "answered_ratio": intelligence.completion_rate(profile),
        "feature_vector": _labelled(intelligence.construct_vector(profile)),
    }


@router.get("/feature-vector")
def feature_vector(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    profile = intelligence.get_profile(db, user.id)
    if not profile:
        return {"completed": False, "feature_vector": None}
    vector = intelligence.construct_vector(profile)
    return {"completed": True, "feature_vector": _labelled(vector), "raw": vector}


@router.get("/status")
def status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    completed = intelligence.get_profile(db, user.id) is not None
    sessions = db.query(AssessmentSession).filter(AssessmentSession.user_id == user.id).count()
    return {"completed": completed, "sessions": sessions}


def _labelled(vector: dict) -> list[dict]:
    """Attach human labels + domain grouping for UI display."""
    return [
        {"construct": c, "label": LABELS.get(c, c), "domain": DOMAIN_OF.get(c, ""),
         "score": vector.get(c, 0.5)}
        for c in ALL_CONSTRUCTS
    ]
