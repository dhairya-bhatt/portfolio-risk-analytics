"""Application configuration and environment variable loading via Pydantic v2."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment or .env file."""

    # Database settings
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/portfolio_risk"
    )

    # Risk calculation defaults
    risk_free_rate: float = 0.0
    trading_days_per_year: int = 252
    default_confidence: float = 0.95

    # Application settings
    app_env: Literal["development", "testing", "production"] = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached accessor for settings singleton."""
    return Settings()
