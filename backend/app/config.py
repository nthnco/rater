from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """App settings, read from environment variables (or the repo-root .env file)."""

    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql+psycopg://rater:rater@localhost:5432/rater"
    tmdb_read_token: str = ""  # TMDB "API Read Access Token" (v4), sent as a Bearer header


settings = Settings()
