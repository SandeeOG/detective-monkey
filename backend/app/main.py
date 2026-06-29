"""Detective Monkey MVP — FastAPI application entrypoint.

Serves the REST API under /api and the single-page web app from /.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR
from .init_db import init_db
from .routers import (
    assessment,
    auth,
    careers,
    chat,
    feedback,
    profile,
    recommendations,
    report,
)

app = FastAPI(title="Detective Monkey", version="0.1.0",
              description="AI Career Intelligence Platform — MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "detective-monkey"}


for r in (auth, profile, assessment, careers, recommendations, chat, feedback, report):
    app.include_router(r.router)

# --- Static SPA ---
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    """Serve static files when they exist; otherwise return the SPA shell so
    client-side routing works on refresh."""
    candidate = STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(STATIC_DIR / "index.html")
