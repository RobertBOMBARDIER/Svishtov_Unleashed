"""
FastAPI application entry point.

Run locally with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Railway detects the ``main.py`` + ``requirements.txt`` combination and runs
the app automatically.  The ``Procfile`` (if present) can override the start
command.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.attractions import router as attractions_router
from app.api.auth import router as auth_router
from app.api.photos import router as photos_router
from app.api.seed import router as seed_router
from app.core.config import settings
from app.core.database import create_tables


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    On startup: create database tables (dev/SQLite) or rely on Alembic
    migrations (production/PostgreSQL).
    """
    await create_tables()
    yield
    # Teardown (if needed) goes here.


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow the Android app (and local development tools) to reach the API.
# In production, restrict ``allow_origins`` to the actual app domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(attractions_router)
app.include_router(photos_router)

# Future routers (added in later tasks):
# from app.api.users import router as users_router
# app.include_router(users_router)


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["meta"], summary="Health check")
async def health() -> dict:
    """Simple liveness probe used by Railway and load balancers."""
    return {"status": "ok", "version": settings.APP_VERSION}
