"""Environment-backed configuration for VOLTA."""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    """Runtime settings loaded from environment variables and `.env`."""

    app_name: str = "VOLTA AI Warranty Intelligence Platform"
    environment: str = "development"
    database_url: str = "sqlite:///data/warranty_tracker.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 720
    refresh_token_expire_days: int = 14
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    allowed_origins: str = "*"
    rate_limit_per_minute: int = 120
    cache_ttl_seconds: int = 60

    @property
    def db_path(self) -> Path:
        """Return the local SQLite path from the configured database URL."""
        if not self.database_url.startswith("sqlite:///"):
            raise ValueError("Only sqlite:/// DATABASE_URL values are supported by this build.")
        return Path(self.database_url.replace("sqlite:///", "", 1))


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings(
        environment=os.getenv("VOLTA_ENV", "development"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///data/warranty_tracker.db"),
        jwt_secret=os.getenv("WARRANTY_APP_SECRET", "dev-secret-change-me"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        allowed_origins=os.getenv("ALLOWED_ORIGINS", "*"),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "120")),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "60")),
    )
