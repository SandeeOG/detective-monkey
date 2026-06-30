"""Student Intelligence Engine — pure pipeline orchestrator.

Runs the deterministic stages end-to-end and returns a canonical
:class:`IntelligenceProfile`. Contains **no** database, FastAPI, recommendation
or LLM logic — its single job is producing student intelligence. This makes the
whole engine testable without running the web app.

    Assessment Responses
        -> validate -> process -> score constructs -> score domains
        -> reliability -> engineer features -> build profile
"""
from __future__ import annotations

from time import perf_counter

from . import (
    construct_scorer,
    domain_scorer,
    feature_engineering,
    processor,
    profile_builder,
    reliability,
    validator,
)
from .types import IntelligenceProfile, QuestionMeta


def run(
    responses: list[tuple[int, float]],
    questions: dict[int, QuestionMeta],
    *,
    student_id: int | None = None,
    session_id: int | None = None,
) -> IntelligenceProfile:
    start = perf_counter()

    clean, report = validator.validate(responses, questions)
    processed = processor.process(clean, questions)
    construct_scores = construct_scorer.score_constructs(processed)
    domain_scores = domain_scorer.score_domains(construct_scores)
    reliability_result = reliability.analyze(processed, report)
    derived_features = feature_engineering.engineer_features(construct_scores)

    execution_ms = (perf_counter() - start) * 1000
    return profile_builder.build(
        construct_scores=construct_scores,
        domain_scores=domain_scores,
        derived_features=derived_features,
        reliability=reliability_result,
        validation=report,
        student_id=student_id,
        session_id=session_id,
        execution_ms=execution_ms,
    )
