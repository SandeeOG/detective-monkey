"""ORM models for the Detective Monkey MVP.

Mirrors the domain model in the PRD: users, profiles, the assessment
subsystem (questions -> sessions -> responses -> construct scores ->
feature vectors), the **normalized Career Knowledge System**, recommendations,
chat and feedback.

The Career Knowledge System (PRD section 13) is the single source of truth for
all career-related information. Careers are normalized into related entities
(skills, subjects, traits, responsibilities, education steps, industries, tools
and career-to-career relations) rather than embedded text/JSON. Two derived
properties — :pyattr:`Career.profile_weights` and
:pyattr:`Career.education_pathway` — keep the recommendation engine, AI coach
and reports working against a stable interface while the underlying data lives
in proper relational tables.
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


# --------------------------------------------------------------------------- #
# Users, profile, assessment (unchanged)
# --------------------------------------------------------------------------- #
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    grade = Column(String, nullable=True)            # e.g. "Grade 10"
    school = Column(String, nullable=True)
    favourite_subjects = Column(JSON, default=list)  # list[str]
    career_aspiration = Column(String, nullable=True)
    location = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)   # e.g. Q-AT-1
    text = Column(Text, nullable=False)
    construct = Column(String, nullable=False, index=True)  # e.g. analytical_thinking
    domain = Column(String, nullable=False)                 # Cognitive/Interests/...
    qtype = Column(String, default="likert")               # likert | mcq
    weight = Column(Float, default=1.0)
    reverse = Column(Boolean, default=False)               # reverse-scored item
    options = Column(JSON, default=list)                   # for mcq: [{label, value}]
    order_index = Column(Integer, default=0)


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, default="in_progress")  # in_progress | completed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    value = Column(Float, nullable=False)  # normalized 1..5 for likert, chosen value for mcq

    session = relationship("AssessmentSession", back_populates="responses")


# --------------------------------------------------------------------------- #
# Student Intelligence Profile (engine V2) — normalized, the single source of
# truth for understanding a student. Replaces the old FeatureVector blob.
# --------------------------------------------------------------------------- #
class StudentIntelligenceProfile(Base):
    """One current canonical intelligence profile per student (with metadata
    and versioning). Child tables hold construct scores, domain scores, derived
    features and reliability metrics."""
    __tablename__ = "intelligence_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=True)
    engine_version = Column(String, nullable=False)
    scoring_version = Column(String, nullable=False)
    assessment_version = Column(String, nullable=False)
    execution_ms = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    construct_scores = relationship("ConstructScore", back_populates="profile", cascade="all, delete-orphan")
    domain_scores = relationship("DomainScore", back_populates="profile", cascade="all, delete-orphan")
    derived_features = relationship("DerivedFeature", back_populates="profile", cascade="all, delete-orphan")
    reliability = relationship(
        "ReliabilityMetric", back_populates="profile", uselist=False, cascade="all, delete-orphan",
    )

    @property
    def vector(self) -> dict[str, float]:
        """Construct-score dict ``{construct: 0..1}`` — the stable interface the
        recommendation engine, AI coach and reports consume (replaces the old
        FeatureVector.vector JSON)."""
        return {cs.construct: cs.score for cs in self.construct_scores}


class ConstructScore(Base):
    __tablename__ = "construct_scores"
    __table_args__ = (UniqueConstraint("profile_id", "construct", name="uq_profile_construct"),)
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("intelligence_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    construct = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    score = Column(Float, nullable=False)  # 0..1

    profile = relationship("StudentIntelligenceProfile", back_populates="construct_scores")


class DomainScore(Base):
    __tablename__ = "domain_scores"
    __table_args__ = (UniqueConstraint("profile_id", "domain", name="uq_profile_domain"),)
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("intelligence_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    domain = Column(String, nullable=False)
    score = Column(Float, nullable=False)  # 0..1

    profile = relationship("StudentIntelligenceProfile", back_populates="domain_scores")


class DerivedFeature(Base):
    __tablename__ = "derived_features"
    __table_args__ = (UniqueConstraint("profile_id", "key", name="uq_profile_feature"),)
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("intelligence_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    value = Column(Float, nullable=False)        # 0..1
    level = Column(String, nullable=False)       # High/Moderate/Developing
    sources = Column(JSON, default=list)         # provenance: construct keys
    explanation = Column(Text, nullable=True)

    profile = relationship("StudentIntelligenceProfile", back_populates="derived_features")


class ReliabilityMetric(Base):
    __tablename__ = "reliability_metrics"
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("intelligence_profiles.id", ondelete="CASCADE"),
                        unique=True, nullable=False, index=True)
    completion_rate = Column(Float, nullable=False)       # 0..1
    response_consistency = Column(Float, nullable=False)  # 0..1
    reliability_score = Column(Float, nullable=False)     # 0..100
    confidence_level = Column(String, nullable=False)     # High/Medium/Low

    profile = relationship("StudentIntelligenceProfile", back_populates="reliability")


# --------------------------------------------------------------------------- #
# Career Knowledge System (normalized)
# --------------------------------------------------------------------------- #

# Simple many-to-many link tables (no extra attributes).
career_subjects = Table(
    "career_subjects", Base.metadata,
    Column("career_id", ForeignKey("careers.id", ondelete="CASCADE"), primary_key=True),
    Column("subject_id", ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True),
)
career_industries = Table(
    "career_industries", Base.metadata,
    Column("career_id", ForeignKey("careers.id", ondelete="CASCADE"), primary_key=True),
    Column("industry_id", ForeignKey("industries.id", ondelete="CASCADE"), primary_key=True),
)
career_tools = Table(
    "career_tools", Base.metadata,
    Column("career_id", ForeignKey("careers.id", ondelete="CASCADE"), primary_key=True),
    Column("tool_id", ForeignKey("tools.id", ondelete="CASCADE"), primary_key=True),
)


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=True)      # Technical/Cognitive/Interpersonal/...
    description = Column(Text, nullable=True)

    career_links = relationship("CareerSkill", back_populates="skill", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)


class Industry(Base):
    __tablename__ = "industries"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)


class Tool(Base):
    __tablename__ = "tools"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)


class Career(Base):
    __tablename__ = "careers"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    subcategory = Column(String, nullable=True)
    summary = Column(String, nullable=True)        # one-line summary
    description = Column(Text, nullable=False)
    difficulty_level = Column(String, nullable=True)   # Beginner/Intermediate/Advanced
    work_environment = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    outlook = Column(String, nullable=True)
    remote_friendly = Column(Boolean, default=False)
    education_level = Column(String, nullable=True)    # highest typical qualification
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    traits = relationship("CareerTrait", back_populates="career", cascade="all, delete-orphan")
    skill_links = relationship("CareerSkill", back_populates="career", cascade="all, delete-orphan")
    responsibilities = relationship(
        "Responsibility", back_populates="career", cascade="all, delete-orphan",
        order_by="Responsibility.order_index",
    )
    education_steps = relationship(
        "EducationStep", back_populates="career", cascade="all, delete-orphan",
        order_by="EducationStep.order_index",
    )
    subjects = relationship("Subject", secondary=career_subjects)
    industries = relationship("Industry", secondary=career_industries)
    tools = relationship("Tool", secondary=career_tools)
    relations = relationship(
        "CareerRelation", foreign_keys="CareerRelation.career_from_id",
        back_populates="from_career", cascade="all, delete-orphan",
    )

    # --- Derived properties (stable interface over the normalized data) ---
    @property
    def profile_weights(self) -> dict[str, float]:
        """Ideal student feature vector ``{construct: ideal_score}``.

        Sourced from the normalized :class:`CareerTrait` rows (replaces the old
        JSON ``profile_weights`` column). The recommendation engine, AI coach and
        reports read this, so they require no changes.
        """
        return {t.construct: t.ideal_score for t in self.traits}

    @property
    def education_pathway(self) -> str:
        """Human-readable pathway assembled from structured education steps.

        Preserves the single-string ``education_pathway`` shape that the report
        and career-detail responses previously returned.
        """
        parts = []
        for step in self.education_steps:
            label = step.title
            if step.optional:
                label += " (optional)"
            parts.append(f"{label}: {step.detail}" if step.detail else label)
        return " ; ".join(parts)


class CareerSkill(Base):
    """Association object linking a career to a skill, with an importance score."""
    __tablename__ = "career_skills"
    __table_args__ = (UniqueConstraint("career_id", "skill_id", name="uq_career_skill"),)
    id = Column(Integer, primary_key=True)
    career_id = Column(Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    importance = Column(Float, default=0.5)  # 0..1 how central this skill is

    career = relationship("Career", back_populates="skill_links")
    skill = relationship("Skill", back_populates="career_links")


class CareerTrait(Base):
    """A personality/aptitude construct a career calls for (replaces profile_weights JSON)."""
    __tablename__ = "career_traits"
    __table_args__ = (UniqueConstraint("career_id", "construct", name="uq_career_trait"),)
    id = Column(Integer, primary_key=True)
    career_id = Column(Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True)
    construct = Column(String, nullable=False, index=True)  # e.g. analytical_thinking
    ideal_score = Column(Float, nullable=False)             # 0..1 target trait level
    importance = Column(Float, default=0.5)                 # 0..1 weight in matching

    career = relationship("Career", back_populates="traits")


class Responsibility(Base):
    __tablename__ = "responsibilities"
    id = Column(Integer, primary_key=True)
    career_id = Column(Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    importance = Column(Float, default=0.5)
    order_index = Column(Integer, default=0)

    career = relationship("Career", back_populates="responsibilities")


class EducationStep(Base):
    __tablename__ = "education_steps"
    id = Column(Integer, primary_key=True)
    career_id = Column(Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String, nullable=False)   # secondary | degree | masters | certification | license
    title = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    optional = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    career = relationship("Career", back_populates="education_steps")


class CareerRelation(Base):
    """Directed career-to-career relation (replaces the related-slugs JSON list)."""
    __tablename__ = "career_relations"
    __table_args__ = (
        UniqueConstraint("career_from_id", "career_to_id", "relation_type", name="uq_career_relation"),
    )
    id = Column(Integer, primary_key=True)
    career_from_id = Column(Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False, index=True)
    career_to_id = Column(Integer, ForeignKey("careers.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String, nullable=False, default="similar")  # similar/specialization/alternative/progression

    from_career = relationship("Career", foreign_keys=[career_from_id], back_populates="relations")
    to_career = relationship("Career", foreign_keys=[career_to_id])


# --------------------------------------------------------------------------- #
# Recommendations, chat, feedback (unchanged)
# --------------------------------------------------------------------------- #
class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    batch_id = Column(String, nullable=False, index=True)  # groups a generation run
    career_id = Column(Integer, ForeignKey("careers.id"), nullable=False)
    score = Column(Float, nullable=False)        # 0..100
    confidence = Column(String, nullable=False)  # High/Medium/Low
    rank = Column(Integer, nullable=False)
    explanation = Column(Text, nullable=True)
    matched_constructs = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    career = relationship("Career")


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, default="New conversation")
    created_at = Column(DateTime, default=datetime.utcnow)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)  # recommendation | assessment | general
    target = Column(String, nullable=True)  # e.g. career slug
    rating = Column(Integer, nullable=True)  # 1..5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
