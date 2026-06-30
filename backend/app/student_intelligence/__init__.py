"""Student Intelligence Engine V2.

A modular, deterministic, explainable pipeline that converts raw assessment
responses into a canonical Student Intelligence Profile — the single source of
truth for understanding a student. Contains no recommendation or LLM logic.

Public entry points:
    from .student_intelligence import service        # DB-backed orchestration
    from .student_intelligence.engine import run      # pure, FastAPI-free pipeline
"""
from . import service
from .config import ENGINE_VERSION
from .engine import run

__all__ = ["service", "run", "ENGINE_VERSION"]
