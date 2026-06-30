"""Stage 1 — Response Validation.

Turns raw (question_id, value) pairs into clean, scorable responses and a
report describing any problems (missing, invalid, out-of-range, duplicate).
Single responsibility: validation only — no scoring.
"""
from __future__ import annotations

from . import config
from .types import QuestionMeta, ValidationReport


def validate(
    responses: list[tuple[int, float]],
    questions: dict[int, QuestionMeta],
) -> tuple[list[tuple[int, float]], ValidationReport]:
    report = ValidationReport(total_questions=len(questions))
    seen: dict[int, float] = {}

    for qid, value in responses:
        if qid not in questions:
            report.invalid.append(qid)          # unknown question
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            report.invalid.append(qid)
            continue
        if v < config.LIKERT_MIN or v > config.LIKERT_MAX:
            report.out_of_range.append(qid)
            v = min(config.LIKERT_MAX, max(config.LIKERT_MIN, v))  # clamp into range
        if qid in seen:
            report.duplicates.append(qid)        # last write wins
        seen[qid] = v

    clean = list(seen.items())
    report.accepted = len(clean)
    report.missing = [qid for qid in questions if qid not in seen]
    report.reverse_items = sum(1 for qid in seen if questions[qid].reverse)
    return clean, report
