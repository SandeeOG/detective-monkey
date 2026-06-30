"""Stage 4 — Domain Scoring.

Aggregates construct scores into domain scores (mean of member constructs).
New domains can be added simply by extending ``config.DOMAINS``.
"""
from __future__ import annotations

from . import config


def score_domains(construct_scores: dict[str, float]) -> dict[str, float]:
    domains: dict[str, float] = {}
    for domain, constructs in config.DOMAINS.items():
        vals = [construct_scores[c] for c in constructs if c in construct_scores]
        domains[domain] = (
            round(sum(vals) / len(vals), config.SCORE_PRECISION) if vals else config.NEUTRAL_SCORE
        )
    return domains
