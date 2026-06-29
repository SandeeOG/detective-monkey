"""Scoring engine: turn raw assessment responses into a Student Feature Vector.

Pipeline (PRD section 10): validate -> apply scoring rules (reverse items) ->
aggregate per construct -> normalise to 0..1.
"""
from collections import defaultdict

from sqlalchemy.orm import Session

from .models import Question
from .seed_data import CONSTRUCTS

LIKERT_MIN, LIKERT_MAX = 1.0, 5.0
ALL_CONSTRUCTS = [c for group in CONSTRUCTS.values() for c in group]


def compute_feature_vector(db: Session, responses: list[tuple[int, float]]) -> dict[str, float]:
    """Aggregate (question_id, value) pairs into a normalised construct vector.

    Each construct score is the mean of its (reverse-adjusted) item values,
    scaled from the 1..5 Likert range to 0..1. Constructs with no responses
    default to a neutral 0.5.
    """
    qmap = {q.id: q for q in db.query(Question).all()}
    buckets: dict[str, list[float]] = defaultdict(list)

    for qid, value in responses:
        q = qmap.get(qid)
        if q is None:
            continue
        v = max(LIKERT_MIN, min(LIKERT_MAX, float(value)))
        if q.reverse:
            v = (LIKERT_MAX + LIKERT_MIN) - v  # 5 -> 1, 1 -> 5
        buckets[q.construct].append(v * (q.weight or 1.0))

    vector: dict[str, float] = {}
    for construct in ALL_CONSTRUCTS:
        items = buckets.get(construct)
        if items:
            mean = sum(items) / len(items)
            vector[construct] = round((mean - LIKERT_MIN) / (LIKERT_MAX - LIKERT_MIN), 4)
        else:
            vector[construct] = 0.5
    return vector
