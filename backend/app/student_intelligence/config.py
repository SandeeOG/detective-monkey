"""Configuration for the Student Intelligence Engine.

All tunable values live here — construct/domain definitions, derived-feature
recipes, normalization rules and reliability thresholds — so the pipeline
contains no hardcoded magic numbers. Construct and domain definitions are
sourced from the assessment seed data to stay compatible with the existing
assessment system.
"""
from ..seed_data import CONSTRUCTS, CONSTRUCT_LABELS

# --- Versioning (stamped onto every generated profile) ---
ENGINE_VERSION = "2.0.0"
SCORING_VERSION = "1.0.0"
ASSESSMENT_VERSION = "1.0"

# --- Likert / normalization rules ---
LIKERT_MIN = 1.0
LIKERT_MAX = 5.0
NEUTRAL_SCORE = 0.5          # default for a construct with no responses
SCORE_PRECISION = 4         # decimal places for scores

# --- Domain definitions (domain -> [construct, ...]) ---
DOMAINS: dict[str, list[str]] = {domain: list(constructs) for domain, constructs in CONSTRUCTS.items()}
ALL_CONSTRUCTS: list[str] = [c for cs in DOMAINS.values() for c in cs]
DOMAIN_OF: dict[str, str] = {c: d for d, cs in DOMAINS.items() for c in cs}
LABELS = dict(CONSTRUCT_LABELS)

# --- Derived feature recipes ---
# Each source is (construct, weight, invert). invert=True uses (1 - score),
# e.g. low security orientation => higher risk tolerance.
DERIVED_FEATURES = [
    {"key": "technology_affinity", "label": "Technology Affinity",
     "sources": [("technology", 0.7, False), ("analytical_thinking", 0.3, False)]},
    {"key": "research_orientation", "label": "Research Orientation",
     "sources": [("analytical_thinking", 0.4, False), ("openness", 0.3, False), ("problem_solving", 0.3, False)]},
    {"key": "business_orientation", "label": "Business Orientation",
     "sources": [("business", 0.6, False), ("leadership", 0.4, False)]},
    {"key": "creative_potential", "label": "Creative Potential",
     "sources": [("arts", 0.6, False), ("openness", 0.4, False)]},
    {"key": "helping_orientation", "label": "Helping Orientation",
     "sources": [("helping_others", 0.6, False), ("healthcare", 0.4, False)]},
    {"key": "leadership_potential", "label": "Leadership Potential",
     "sources": [("leadership", 0.5, False), ("extraversion", 0.25, False), ("conscientiousness", 0.25, False)]},
    {"key": "entrepreneurial_potential", "label": "Entrepreneurial Potential",
     "sources": [("entrepreneurship", 0.5, False), ("leadership", 0.25, False), ("openness", 0.25, False)]},
    {"key": "risk_tolerance", "label": "Risk Tolerance",
     "sources": [("entrepreneurship", 0.4, False), ("openness", 0.3, False), ("security", 0.3, True)]},
    {"key": "social_orientation", "label": "Social Orientation",
     "sources": [("extraversion", 0.4, False), ("teamwork", 0.3, False), ("helping_others", 0.3, False)]},
    {"key": "learning_agility", "label": "Learning Agility",
     "sources": [("openness", 0.4, False), ("problem_solving", 0.3, False), ("analytical_thinking", 0.3, False)]},
]

# Derived-feature level thresholds (value 0..1 -> label).
FEATURE_LEVELS = [(0.72, "High"), (0.50, "Moderate"), (0.0, "Developing")]

# --- Reliability ---
RELIABILITY_WEIGHTS = {"completion": 0.5, "consistency": 0.5}
# reliability_score (0..100) -> confidence band
CONFIDENCE_THRESHOLDS = [(75.0, "High"), (50.0, "Medium"), (0.0, "Low")]
