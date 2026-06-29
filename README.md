# 🐵 Detective Monkey — MVP

An AI-powered **Career Intelligence Platform** for students (Grades 8–12). This is
a runnable MVP built from the product specs in `Career Prediction/`, covering the
full FR-001 → FR-008 scope:

| FR | Feature | Status |
|----|---------|--------|
| FR-001 | User registration / login / sessions | ✅ |
| FR-002 | Student profile | ✅ |
| FR-003 | Assessment engine → Student Feature Vector | ✅ |
| FR-004 | Rules-based recommendation engine | ✅ |
| FR-005 | Career explorer + knowledge base | ✅ |
| FR-006 | AI career coach (chat) | ✅ |
| FR-007 | Printable career report | ✅ |
| FR-008 | Feedback collection | ✅ |

## Architecture

- **Backend:** FastAPI + SQLAlchemy + SQLite — REST API under `/api`.
  - Assessment scoring (`scoring.py`): responses → construct scores → normalised feature vector.
  - Recommendation engine (`recommender.py`): transparent weighted-similarity matching with explanations + skill gaps.
  - AI coach (`coach.py`): provider-agnostic LLM layer (`app/llm/`) — Anthropic, Gemini, or a deterministic offline fallback, selected via `LLM_PROVIDER`.
- **Frontend:** responsive vanilla-JS single-page app served by the same server (no build step).
- **Data:** 16 psychometric constructs, a 32-item question bank, and 14 seeded careers.

The LLM is an **explanation layer only** — scores and rankings come from the
deterministic engine, matching the PRD's "guidance, not prediction" principle.

## Run it

```bash
cd detective-monkey
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cd backend
uvicorn app.main:app --reload
```

Then open **http://localhost:8000**. The SQLite DB and seed data are created
automatically on first run.

### Optional: live AI coach (provider-agnostic)

By default the coach gives helpful deterministic answers (offline fallback). To
use a real LLM, set three generic environment variables — no code changes
needed:

```bash
# Windows PowerShell
$env:LLM_PROVIDER = "anthropic"        # or "gemini"
$env:LLM_API_KEY  = "your-api-key"
$env:LLM_MODEL    = "claude-sonnet-4-6" # optional; provider has a sensible default

# macOS/Linux
export LLM_PROVIDER=anthropic
export LLM_API_KEY=your-api-key
```

| `LLM_PROVIDER` | SDK to install | Default model |
|----------------|----------------|---------------|
| `anthropic` (aliases: `claude`) | `anthropic` | `claude-sonnet-4-6` |
| `gemini` (aliases: `google`) | `google-genai` | `gemini-2.0-flash` |
| unset / `fallback` | none | offline deterministic |

If a configured provider errors at runtime, the coach degrades gracefully to the
offline fallback. **Adding a new provider** (OpenAI, Ollama, …) is a one-liner:
implement `LLMProvider` in `app/llm/providers/` and register it in
`app/llm/factory.py`.

## Try the flow

1. Create an account.
2. Fill in your profile (optional).
3. Complete the assessment (~5 min).
4. View your ranked career matches + strength bars.
5. Explore careers, chat with the AI coach, download your report.

## API

Interactive docs at **http://localhost:8000/docs** once running.

## Out of MVP scope

Parent/teacher/school portals, scholarship & college recommendation, resume
builder, native mobile app — see `Career Prediction/02_PRD/03_Product_Scope.md`.
