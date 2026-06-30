"""Stage 3 — Construct Scoring.

Aggregates processed responses into one normalized score per construct (0..1).
Each construct is scored independently. Constructs with no responses default to
the neutral score. The math is intentionally identical to the original MVP
feature-vector calculation, so downstream consumers see the same values.
"""
from __future__ import annotations

from collections import defaultdict

from . import config
from .types import ProcessedResponse


def score_constructs(processed: list[ProcessedResponse]) -> dict[str, float]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for r in processed:
        buckets[r.construct].append(r.value * r.weight)

    scores: dict[str, float] = {}
    span = config.LIKERT_MAX - config.LIKERT_MIN
    for construct in config.ALL_CONSTRUCTS:
        items = buckets.get(construct)
        if items:
            mean = sum(items) / len(items)
            scores[construct] = round((mean - config.LIKERT_MIN) / span, config.SCORE_PRECISION)
        else:
            scores[construct] = config.NEUTRAL_SCORE
    return scores
