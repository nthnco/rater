from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """App settings, read from environment variables (or the repo-root .env file)."""

    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rater:rater@localhost:5432/rater"
    tmdb_read_token: str = ""  # TMDB "API Read Access Token" (v4), sent as a Bearer header

    # Auth. The default secret is for local dev only; production must set JWT_SECRET (Phase 4).
    # HS256 secrets should be at least 32 bytes (RFC 7518 §3.2); a short or empty one fails at
    # startup rather than silently signing tokens with a weak key.
    jwt_secret: str = Field(
        default="dev-only-insecure-jwt-secret-change-me-in-production", min_length=32
    )
    jwt_ttl_days: int = 7
    cookie_secure: bool = False  # True in production (HTTPS only)


settings = Settings()
