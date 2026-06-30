"""Career Explorer & Knowledge System (FR-005 / PRD section 13).

Serializes the normalized Career Knowledge System. Existing response keys and
types are preserved for backward compatibility (the web app reads
``responsibilities``/``skills``/``subjects`` as string lists, ``education_pathway``
as a string and ``related`` as objects); normalized data is exposed additively
under new keys (``summary``, ``skills_detailed``, ``traits``, ``industries`` …).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Career

router = APIRouter(prefix="/api/careers", tags=["careers"])


def _skill_names(c: Career) -> list[str]:
    return [link.skill.name for link in c.skill_links]


def _summary(c: Career) -> dict:
    # Existing keys preserved; new scalar fields added additively.
    return {
        "slug": c.slug, "name": c.name, "category": c.category,
        "description": c.description, "salary_range": c.salary_range,
        "outlook": c.outlook, "work_environment": c.work_environment,
        # enriched
        "subcategory": c.subcategory, "summary": c.summary,
        "difficulty_level": c.difficulty_level, "remote_friendly": c.remote_friendly,
        "education_level": c.education_level,
    }


def _detail(c: Career) -> dict:
    related = [
        {"slug": rel.to_career.slug, "name": rel.to_career.name,
         "category": rel.to_career.category, "relation_type": rel.relation_type}
        for rel in c.relations if rel.to_career is not None
    ]
    return {
        **_summary(c),
        # --- legacy-compatible shapes (unchanged types) ---
        "responsibilities": [r.title for r in c.responsibilities],
        "skills": _skill_names(c),
        "subjects": [s.name for s in c.subjects],
        "education_pathway": c.education_pathway,   # derived string
        "related": related,
        # --- enriched normalized data (additive) ---
        "skills_detailed": [
            {"name": link.skill.name, "category": link.skill.category,
             "description": link.skill.description, "importance": link.importance}
            for link in c.skill_links
        ],
        "responsibilities_detailed": [
            {"title": r.title, "description": r.description, "importance": r.importance}
            for r in c.responsibilities
        ],
        "education_steps": [
            {"stage": e.stage, "title": e.title, "detail": e.detail, "optional": e.optional}
            for e in c.education_steps
        ],
        "traits": [
            {"construct": t.construct, "ideal_score": t.ideal_score, "importance": t.importance}
            for t in c.traits
        ],
        "industries": [i.name for i in c.industries],
        "tools": [t.name for t in c.tools],
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
            or term in (c.summary or "").lower()
            or any(term in s.lower() for s in _skill_names(c))
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
    return _detail(c)
