"""
SQLAlchemy async engine and session factory.

Usage
-----
Import ``async_session_factory`` for dependency injection, or use the
``get_db`` dependency from ``app.dependencies`` in FastAPI route handlers.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.base import Base  # noqa: F401 — re-exported for Alembic

# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    # Pool settings suitable for both SQLite (dev) and PostgreSQL (prod).
    # asyncpg handles its own connection pool; for aiosqlite we keep it simple.
    pool_pre_ping=True,
)

# ── Session factory ───────────────────────────────────────────────────────────

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def create_tables() -> None:
    """
    Create all tables defined in the ORM models.

    Called at application startup (``main.py`` lifespan) for development /
    SQLite environments.  In production, Alembic migrations handle schema
    changes instead.
    """
    # Import here to ensure all models are registered on Base.metadata
    import app.models  # noqa: F401 — registers Attraction, Photo, User

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
