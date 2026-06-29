"""Application configuration.

All settings are read from environment variables with sensible defaults so the
MVP runs out-of-the-box with zero configuration.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend

# --- Core ---
SECRET_KEY = os.getenv("DM_SECRET_KEY", "dev-secret-change-me-in-production")
TOKEN_TTL_SECONDS = int(os.getenv("DM_TOKEN_TTL", str(60 * 60 * 24 * 7)))  # 7 days
DATABASE_URL = os.getenv("DM_DATABASE_URL", f"sqlite:///{BASE_DIR / 'detective_monkey.db'}")

# --- AI Coach (LLM) ---
# If ANTHROPIC_API_KEY is set the coach uses Claude; otherwise a deterministic
# template-based explainer is used so the feature works with no external deps.
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("DM_LLM_MODEL", "claude-sonnet-4-6")

STATIC_DIR = BASE_DIR / "static"
