"""Stage 6 — Feature Engineering.

Converts construct scores into reusable, explainable derived features using the
deterministic recipes in ``config.DERIVED_FEATURES``. Every feature records the
constructs that produced it (provenance) and a human-readable explanation, so
the engine can always answer "why does this feature exist?".
"""
from __future__ import annotations

from . import config
from .types import DerivedFeatureResult


def _level(value: float) -> str:
    for threshold, label in config.FEATURE_LEVELS:
        if value >= threshold:
            return label
    return config.FEATURE_LEVELS[-1][1]


def engineer_features(construct_scores: dict[str, float]) -> list[DerivedFeatureResult]:
    features: list[DerivedFeatureResult] = []
    for spec in config.DERIVED_FEATURES:
        total_w = 0.0
        acc = 0.0
        sources: list[str] = []
        for construct, weight, invert in spec["sources"]:
            score = construct_scores.get(construct, config.NEUTRAL_SCORE)
            contribution = (1.0 - score) if invert else score
            acc += contribution * weight
            total_w += weight
            sources.append(construct)
        value = round(acc / total_w, config.SCORE_PRECISION) if total_w else config.NEUTRAL_SCORE
        level = _level(value)

        source_labels = [config.LABELS.get(c, c) for c in sources]
        explanation = (
            f"{level} {spec['label']} derived from "
            f"{', '.join(source_labels)}."
        )
        features.append(DerivedFeatureResult(
            key=spec["key"], label=spec["label"], value=value, level=level,
            sources=sources, explanation=explanation,
        ))
    return features
