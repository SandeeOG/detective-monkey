"""AI Career Coach chat (FR-006 / PRD section 12)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..coach import generate_reply
from ..database import get_db
from ..deps import get_current_user
from ..models import Conversation, Message, Profile, Recommendation, User
from ..recommender import _skill_gaps  # reuse skill-gap helper for fallback hints
from ..schemas import ChatIn
from ..student_intelligence import service as intelligence

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _student_context(db: Session, user: User):
    profile_row = db.query(Profile).filter(Profile.user_id == user.id).first()
    profile = {
        "full_name": user.full_name,
        "grade": getattr(profile_row, "grade", None),
        "favourite_subjects": getattr(profile_row, "favourite_subjects", []) or [],
        "career_aspiration": getattr(profile_row, "career_aspiration", None),
    }
    intel = intelligence.get_profile(db, user.id)
    vector = intelligence.construct_vector(intel) if intel else None

    recs = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.rank)
        .all()
    )
    rec_ctx = [{
        "name": r.career.name,
        "score": r.score,
        "confidence": r.confidence,
        "explanation": r.explanation,
        "skill_gaps": [],  # populated below for the top match only
    } for r in recs]

    # Provide skill-gap hints for the top match so the coach can answer "what to learn".
    if recs and vector:
        top_career = recs[0].career
        from ..recommender import _career_score
        _, contributions = _career_score(vector, top_career.profile_weights or {})
        rec_ctx[0]["skill_gaps"] = _skill_gaps(contributions)

    return profile, vector, rec_ctx


@router.post("")
def chat(payload: ChatIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.conversation_id:
        conv = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id, Conversation.user_id == user.id
        ).first()
        if not conv:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = Conversation(user_id=user.id, title=payload.message[:48])
        db.add(conv)
        db.flush()

    history = [{"role": m.role, "content": m.content} for m in conv.messages]
    db.add(Message(conversation_id=conv.id, role="user", content=payload.message))

    profile, vector, rec_ctx = _student_context(db, user)
    reply = generate_reply(payload.message, profile, vector, rec_ctx, history)

    db.add(Message(conversation_id=conv.id, role="assistant", content=reply))
    db.commit()
    return {"conversation_id": conv.id, "reply": reply}


@router.get("/history")
def history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    convs = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    out = []
    for c in convs:
        out.append({
            "id": c.id,
            "title": c.title,
            "messages": [
                {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
                for m in c.messages
            ],
        })
    return {"conversations": out}


@router.delete("/history")
def clear_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(Conversation).filter(Conversation.user_id == user.id).delete()
    db.commit()
    return {"ok": True}
