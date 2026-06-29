"""Assessment engine endpoints (FR-003 / PRD section 10)."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import AssessmentSession, FeatureVector, Question, Response, User
from ..schemas import SubmitIn
from ..scoring import ALL_CONSTRUCTS, compute_feature_vector
from ..seed_data import CONSTRUCTS, CONSTRUCT_LABELS

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.get("/questions")
def get_questions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Return the question bank grouped by domain (no scoring metadata leaked)."""
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
    total_questions = db.query(Question).count()
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

    vector = compute_feature_vector(db, pairs)
    answered_ratio = round(len(pairs) / total_questions, 3) if total_questions else 0.0

    fv = db.query(FeatureVector).filter(FeatureVector.user_id == user.id).first()
    if fv:
        fv.vector = vector
        fv.session_id = session.id
        fv.created_at = datetime.utcnow()
    else:
        db.add(FeatureVector(user_id=user.id, session_id=session.id, vector=vector))
    db.commit()
    return {
        "session_id": session.id,
        "answered_ratio": answered_ratio,
        "feature_vector": _labelled(vector),
    }


@router.get("/feature-vector")
def feature_vector(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fv = db.query(FeatureVector).filter(FeatureVector.user_id == user.id).first()
    if not fv:
        return {"completed": False, "feature_vector": None}
    return {"completed": True, "feature_vector": _labelled(fv.vector), "raw": fv.vector}


@router.get("/status")
def status(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fv = db.query(FeatureVector).filter(FeatureVector.user_id == user.id).first()
    sessions = db.query(AssessmentSession).filter(AssessmentSession.user_id == user.id).count()
    return {"completed": fv is not None, "sessions": sessions}


def _labelled(vector: dict) -> list[dict]:
    """Attach human labels + domain grouping for UI display."""
    domain_of = {c: d for d, cs in CONSTRUCTS.items() for c in cs}
    out = []
    for c in ALL_CONSTRUCTS:
        out.append({
            "construct": c,
            "label": CONSTRUCT_LABELS.get(c, c),
            "domain": domain_of.get(c, ""),
            "score": vector.get(c, 0.5),
        })
    return out
