"""Stage 5 — Reliability Analysis.

Measures assessment quality deterministically:

* completion_rate — share of the question bank that was answered.
* response_consistency — agreement within each construct's items (after reverse
  scoring). Contradictory answers (e.g. agreeing with a statement *and* its
  opposite) widen a construct's spread and lower consistency.

These combine into a 0..100 reliability score and a confidence band that the
recommendation engine can later use to temper its confidence.
"""
from __future__ import annotations

from collections import defaultdict

from . import config
from .types import ProcessedResponse, ReliabilityResult, ValidationReport


def _confidence(score: float) -> str:
    for threshold, label in config.CONFIDENCE_THRESHOLDS:
        if score >= threshold:
            return label
    return config.CONFIDENCE_THRESHOLDS[-1][1]


def analyze(
    processed: list[ProcessedResponse],
    report: ValidationReport,
) -> ReliabilityResult:
    total = report.total_questions or 1
    completion_rate = round(report.accepted / total, config.SCORE_PRECISION)

    # Consistency: per construct, how tightly its (reverse-aligned) items agree.
    by_construct: dict[str, list[float]] = defaultdict(list)
    for r in processed:
        by_construct[r.construct].append(r.value)

    span = config.LIKERT_MAX - config.LIKERT_MIN
    spreads = []
    for values in by_construct.values():
        if len(values) >= 2:
            spreads.append((max(values) - min(values)) / span)
    response_consistency = round(1.0 - (sum(spreads) / len(spreads)), config.SCORE_PRECISION) if spreads else 1.0

    w = config.RELIABILITY_WEIGHTS
    reliability_score = round(
        (w["completion"] * completion_rate + w["consistency"] * response_consistency) * 100, 1
    )
    return ReliabilityResult(
        completion_rate=completion_rate,
        response_consistency=response_consistency,
        reliability_score=reliability_score,
        confidence_level=_confidence(reliability_score),
    )
