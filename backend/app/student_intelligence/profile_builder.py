"""Stage 7 — Profile Builder.

Assembles the canonical :class:`IntelligenceProfile` from the outputs of the
earlier stages plus metadata/versioning. No calculation happens here — it only
composes results.
"""
from __future__ import annotations

from datetime import datetime

from . import config
from .types import (
    DerivedFeatureResult,
    IntelligenceProfile,
    ReliabilityResult,
    ValidationReport,
)


def build(
    *,
    construct_scores: dict[str, float],
    domain_scores: dict[str, float],
    derived_features: list[DerivedFeatureResult],
    reliability: ReliabilityResult,
    validation: ValidationReport,
    student_id: int | None,
    session_id: int | None,
    execution_ms: float,
) -> IntelligenceProfile:
    metadata = {
        "student_id": student_id,
        "session_id": session_id,
        "generated_at": datetime.utcnow().isoformat(),
        "engine_version": config.ENGINE_VERSION,
        "scoring_version": config.SCORING_VERSION,
        "assessment_version": config.ASSESSMENT_VERSION,
        "execution_ms": round(execution_ms, 3),
    }
    return IntelligenceProfile(
        metadata=metadata,
        construct_scores=construct_scores,
        domain_scores=domain_scores,
        derived_features=derived_features,
        reliability=reliability,
        validation=validation,
    )
