"""ORM models for the Detective Monkey MVP.

Mirrors the domain model in the PRD: users, profiles, the assessment
subsystem (questions -> sessions -> responses -> construct scores ->
feature vectors), the career knowledge base, recommendations, chat and
feedback.
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
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


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


class FeatureVector(Base):
    """Latest computed feature vector per user (construct -> 0..1)."""
    __tablename__ = "feature_vectors"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=True)
    vector = Column(JSON, default=dict)   # {construct: float}
    created_at = Column(DateTime, default=datetime.utcnow)


class Career(Base):
    __tablename__ = "careers"
    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    responsibilities = Column(JSON, default=list)
    skills = Column(JSON, default=list)
    subjects = Column(JSON, default=list)
    education_pathway = Column(Text, nullable=True)
    work_environment = Column(String, nullable=True)
    salary_range = Column(String, nullable=True)
    outlook = Column(String, nullable=True)
    related = Column(JSON, default=list)         # list[slug]
    profile_weights = Column(JSON, default=dict)  # {construct: target 0..1} ideal profile


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
