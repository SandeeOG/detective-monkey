"""Application configuration.

All settings are read from environment variables with sensible defaults so the
MVP runs out-of-the-box with zero configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # .../backend
load_dotenv(BASE_DIR / ".env")

# --- Core ---
SECRET_KEY = os.getenv("DM_SECRET_KEY", "dev-secret-change-me-in-production")
TOKEN_TTL_SECONDS = int(os.getenv("DM_TOKEN_TTL", str(60 * 60 * 24 * 7)))  # 7 days
DATABASE_URL = os.getenv("DM_DATABASE_URL", f"sqlite:///{BASE_DIR / 'detective_monkey.db'}")

# --- AI Coach (LLM) ---
# Provider selection is environment-driven and handled by app.llm.factory:
#   LLM_PROVIDER  (anthropic | gemini | fallback; default: fallback)
#   LLM_API_KEY   API key for the selected provider
#   LLM_MODEL     optional model id override
# With no provider configured the coach uses a deterministic offline fallback,
# so the feature works out-of-the-box with no external dependencies.

STATIC_DIR = BASE_DIR / "static"
