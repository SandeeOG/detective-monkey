"""Create tables and seed the question bank + career knowledge base.

Idempotent: safe to call on every startup. Seeds only run when the relevant
tables are empty.
"""
from .database import Base, SessionLocal, engine
from .models import Career, Question
from .seed_data import CAREERS, QUESTIONS


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Question).count() == 0:
            for i, (code, text, construct, domain, reverse) in enumerate(QUESTIONS):
                db.add(Question(
                    code=code, text=text, construct=construct, domain=domain,
                    qtype="likert", weight=1.0, reverse=reverse, options=[], order_index=i,
                ))
        if db.query(Career).count() == 0:
            for c in CAREERS:
                db.add(Career(
                    slug=c["slug"], name=c["name"], category=c["category"],
                    description=c["description"], responsibilities=c["responsibilities"],
                    skills=c["skills"], subjects=c["subjects"],
                    education_pathway=c["education_pathway"], work_environment=c["work_environment"],
                    salary_range=c["salary_range"], outlook=c["outlook"], related=c["related"],
                    profile_weights=c["profile_weights"],
                ))
        db.commit()
    finally:
        db.close()
