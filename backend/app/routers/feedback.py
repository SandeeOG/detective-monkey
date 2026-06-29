"""Feedback collection (FR-008)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Feedback, User
from ..schemas import FeedbackIn

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", status_code=201)
def submit_feedback(payload: FeedbackIn, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    fb = Feedback(
        user_id=user.id, kind=payload.kind, target=payload.target,
        rating=payload.rating, comment=payload.comment,
    )
    db.add(fb)
    db.commit()
    return {"ok": True}


@router.get("")
def my_feedback(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Feedback).filter(Feedback.user_id == user.id).order_by(Feedback.created_at.desc()).all()
    return {"feedback": [
        {"kind": r.kind, "target": r.target, "rating": r.rating,
         "comment": r.comment, "created_at": r.created_at.isoformat()}
        for r in rows
    ]}
