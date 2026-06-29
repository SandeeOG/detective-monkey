"""Pydantic request/response schemas."""
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class RegisterIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    token: str
    user: dict


# --- Profile ---
class ProfileIn(BaseModel):
    grade: str | None = None
    school: str | None = None
    favourite_subjects: list[str] = []
    career_aspiration: str | None = None
    location: str | None = None


# --- Assessment ---
class ResponseIn(BaseModel):
    question_id: int
    value: float


class SubmitIn(BaseModel):
    session_id: int
    responses: list[ResponseIn]


# --- Chat ---
class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: int | None = None


# --- Feedback ---
class FeedbackIn(BaseModel):
    kind: str = Field(pattern="^(recommendation|assessment|general)$")
    target: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
