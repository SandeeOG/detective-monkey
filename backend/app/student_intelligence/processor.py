"""Stage 2 — Response Processing.

Standardizes clean responses: applies reverse scoring and attaches construct /
domain / weight metadata. No aggregation or business logic here.
"""
from __future__ import annotations

from . import config
from .types import ProcessedResponse, QuestionMeta


def process(
    clean: list[tuple[int, float]],
    questions: dict[int, QuestionMeta],
) -> list[ProcessedResponse]:
    out: list[ProcessedResponse] = []
    for qid, value in clean:
        q = questions[qid]
        v = value
        if q.reverse:
            # Reflect onto the same direction as positively-keyed items.
            v = (config.LIKERT_MAX + config.LIKERT_MIN) - v
        out.append(ProcessedResponse(
            question_id=qid, construct=q.construct, domain=q.domain,
            value=v, weight=q.weight,
        ))
    return out
