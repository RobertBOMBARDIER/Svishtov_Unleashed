"""
Application settings loaded from environment variables.

Uses pydantic-settings so every variable can be overridden via a .env file
or Railway Dashboard environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./svishtov_dev.db"
    """
    Async SQLAlchemy connection string.
    Railway injects a PostgreSQL URL like:
      postgresql+asyncpg://user:pass@host:5432/dbname
    For local development the default falls back to an async SQLite file.
    """

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production-use-a-long-random-string"
    """
    Secret key used to sign JWT tokens (HS256).
    MUST be overridden in production via the Railway environment variable.
    """

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours default

    # ── Photo storage ─────────────────────────────────────────────────────────
    STORAGE_PATH: str = "/data/photos"
    """
    Filesystem path where uploaded photos and thumbnails are stored.
    Railway mounts a persistent volume here.
    """

    # ── App ───────────────────────────────────────────────────────────────────
    APP_TITLE: str = "Svishtov Tourist Guide API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


# Singleton instance — import this everywhere
settings = Settings()
