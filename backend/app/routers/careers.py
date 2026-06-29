"""Career Explorer & Knowledge System (FR-005 / PRD section 13)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Career

router = APIRouter(prefix="/api/careers", tags=["careers"])


def _summary(c: Career) -> dict:
    return {
        "slug": c.slug, "name": c.name, "category": c.category,
        "description": c.description, "salary_range": c.salary_range,
        "outlook": c.outlook, "work_environment": c.work_environment,
    }


def _detail(c: Career, db: Session) -> dict:
    related = []
    if c.related:
        related = [
            {"slug": r.slug, "name": r.name, "category": r.category}
            for r in db.query(Career).filter(Career.slug.in_(c.related)).all()
        ]
    return {
        **_summary(c),
        "responsibilities": c.responsibilities or [],
        "skills": c.skills or [],
        "subjects": c.subjects or [],
        "education_pathway": c.education_pathway,
        "related": related,
    }


@router.get("")
def list_careers(
    db: Session = Depends(get_db),
    q: str | None = Query(default=None),
    category: str | None = Query(default=None),
):
    query = db.query(Career)
    if category:
        query = query.filter(Career.category == category)
    careers = query.order_by(Career.name).all()
    if q:
        term = q.lower()
        careers = [
            c for c in careers
            if term in c.name.lower()
            or term in (c.description or "").lower()
            or any(term in s.lower() for s in (c.skills or []))
        ]
    return {"careers": [_summary(c) for c in careers]}


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    rows = db.query(Career.category).distinct().all()
    return {"categories": sorted({r[0] for r in rows})}


@router.get("/{slug}")
def career_detail(slug: str, db: Session = Depends(get_db)):
    c = db.query(Career).filter(Career.slug == slug).first()
    if not c:
        raise HTTPException(404, "Career not found")
    return _detail(c, db)
