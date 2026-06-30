"""Plain, framework-free data types passed between pipeline stages.

These dataclasses keep the engine pure and fully testable without FastAPI or a
database. The service layer maps them to/from ORM rows.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QuestionMeta:
    """Scoring metadata for one assessment question."""
    id: int
    construct: str
    domain: str
    weight: float = 1.0
    reverse: bool = False


@dataclass
class ValidationReport:
    accepted: int = 0
    total_questions: int = 0
    missing: list[int] = field(default_factory=list)        # unanswered question ids
    invalid: list[int] = field(default_factory=list)        # non-numeric / unscorable
    out_of_range: list[int] = field(default_factory=list)   # outside the Likert range
    duplicates: list[int] = field(default_factory=list)     # repeated question ids
    reverse_items: int = 0


@dataclass(frozen=True)
class ProcessedResponse:
    question_id: int
    construct: str
    domain: str
    value: float        # reverse-applied value on the Likert scale
    weight: float


@dataclass(frozen=True)
class DerivedFeatureResult:
    key: str
    label: str
    value: float
    level: str
    sources: list[str]      # construct keys that fed this feature (provenance)
    explanation: str


@dataclass(frozen=True)
class ReliabilityResult:
    completion_rate: float       # 0..1
    response_consistency: float  # 0..1
    reliability_score: float     # 0..100
    confidence_level: str        # High/Medium/Low


@dataclass
class IntelligenceProfile:
    """The canonical Student Intelligence Profile (engine output)."""
    metadata: dict
    construct_scores: dict[str, float]
    domain_scores: dict[str, float]
    derived_features: list[DerivedFeatureResult]
    reliability: ReliabilityResult
    validation: ValidationReport
