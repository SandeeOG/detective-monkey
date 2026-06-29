"""Student profile (FR-002)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Profile, User
from ..schemas import ProfileIn

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _serialize(user: User, profile: Profile) -> dict:
    return {
        "full_name": user.full_name,
        "email": user.email,
        "grade": profile.grade,
        "school": profile.school,
        "favourite_subjects": profile.favourite_subjects or [],
        "career_aspiration": profile.career_aspiration,
        "location": profile.location,
    }


def _get_or_create(db: Session, user: User) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()
    if not profile:
        profile = Profile(user_id=user.id, favourite_subjects=[])
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("")
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _serialize(user, _get_or_create(db, user))


@router.put("")
def update_profile(payload: ProfileIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    profile = _get_or_create(db, user)
    profile.grade = payload.grade
    profile.school = payload.school
    profile.favourite_subjects = payload.favourite_subjects
    profile.career_aspiration = payload.career_aspiration
    profile.location = payload.location
    db.commit()
    db.refresh(profile)
    return _serialize(user, profile)
