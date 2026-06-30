"""Create tables and seed the question bank + normalized Career Knowledge System.

Idempotent: safe to call on every startup. Seeds only run when the relevant
tables are empty.
"""
from .database import Base, SessionLocal, engine
from .models import (
    Career,
    CareerRelation,
    CareerSkill,
    CareerTrait,
    EducationStep,
    Industry,
    Question,
    Responsibility,
    Skill,
    Subject,
    Tool,
)
from .seed_data import (
    CAREERS,
    INDUSTRIES,
    QUESTIONS,
    SKILLS,
    SUBJECTS,
    TOOLS,
)


def _seed_questions(db) -> None:
    if db.query(Question).count():
        return
    for i, (code, text, construct, domain, reverse) in enumerate(QUESTIONS):
        db.add(Question(
            code=code, text=text, construct=construct, domain=domain,
            qtype="likert", weight=1.0, reverse=reverse, options=[], order_index=i,
        ))


def _seed_registries(db):
    """Create the shared skill/subject/industry/tool vocabularies; return name->row maps."""
    skills = {}
    for name, (category, description) in SKILLS.items():
        row = Skill(name=name, category=category, description=description)
        db.add(row)
        skills[name] = row

    subjects = {}
    for name in SUBJECTS:
        row = Subject(name=name)
        db.add(row)
        subjects[name] = row

    industries = {}
    for name in INDUSTRIES:
        row = Industry(name=name)
        db.add(row)
        industries[name] = row

    tools = {}
    for name in TOOLS:
        row = Tool(name=name)
        db.add(row)
        tools[name] = row

    return skills, subjects, industries, tools


def _get_or_create(registry, db, model, name):
    """Fetch a registry row, creating it on the fly if a career references a
    value missing from the master list (keeps seeding resilient)."""
    row = registry.get(name)
    if row is None:
        row = model(name=name)
        db.add(row)
        registry[name] = row
    return row


def _seed_careers(db) -> None:
    if db.query(Career).count():
        return

    skills, subjects, industries, tools = _seed_registries(db)
    by_slug: dict[str, Career] = {}

    for c in CAREERS:
        career = Career(
            slug=c["slug"], name=c["name"], category=c["category"],
            subcategory=c.get("subcategory"), summary=c.get("summary"),
            description=c["description"], difficulty_level=c.get("difficulty_level"),
            work_environment=c.get("work_environment"), salary_range=c.get("salary_range"),
            outlook=c.get("outlook"), remote_friendly=c.get("remote_friendly", False),
            education_level=c.get("education_level"),
        )

        # Traits — importance defaults to ideal_score, preserving the original
        # recommendation business logic exactly.
        for construct, ideal in c.get("traits", {}).items():
            career.traits.append(CareerTrait(construct=construct, ideal_score=ideal, importance=ideal))

        # Skills (with importance) via the association object.
        for skill_name, importance in c.get("skills", []):
            skill = _get_or_create(skills, db, Skill, skill_name)
            career.skill_links.append(CareerSkill(skill=skill, importance=importance))

        # Responsibilities (ordered, structured).
        for i, (title, desc, importance) in enumerate(c.get("responsibilities", [])):
            career.responsibilities.append(
                Responsibility(title=title, description=desc, importance=importance, order_index=i)
            )

        # Education steps (ordered, structured).
        for i, (stage, title, detail, optional) in enumerate(c.get("education", [])):
            career.education_steps.append(
                EducationStep(stage=stage, title=title, detail=detail, optional=optional, order_index=i)
            )

        # Many-to-many vocabularies.
        career.subjects = [_get_or_create(subjects, db, Subject, n) for n in c.get("subjects", [])]
        career.industries = [_get_or_create(industries, db, Industry, n) for n in c.get("industries", [])]
        career.tools = [_get_or_create(tools, db, Tool, n) for n in c.get("tools", [])]

        db.add(career)
        by_slug[c["slug"]] = career

    db.flush()  # assign ids before wiring relations

    # Career-to-career relations (resolved by slug).
    for c in CAREERS:
        src = by_slug[c["slug"]]
        for to_slug, rel_type in c.get("relations", []):
            target = by_slug.get(to_slug)
            if target is not None:
                src.relations.append(CareerRelation(career_to_id=target.id, relation_type=rel_type))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_questions(db)
        _seed_careers(db)
        db.commit()
    finally:
        db.close()
