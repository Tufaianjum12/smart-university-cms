"""
Centralized application configuration.

Every environment-dependent value (database URL, secret key, allowed CORS
origins, etc.) is read ONCE here, from environment variables, and exposed
as a single `settings` object that the rest of the app imports.

Why centralize this instead of calling os.getenv() all over the codebase?
- One place to see every setting the app depends on.
- Pydantic validates types and required-ness at startup, so a missing
  DATABASE_URL fails immediately and loudly instead of crashing later
  deep inside a request.
- Easy to swap how config is loaded (e.g. from a secrets manager in AWS
  later) without touching the rest of the app.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    ENVIRONMENT: str = "development"  # development | testing | production
    APP_NAME: str = "Smart University CMS API"
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    # Phase 1 only needs this to exist and be connectable. No tables yet.
    DATABASE_URL: str

    # --- Security (used starting Phase 3, but the config slot exists now
    # so nothing has to be redesigned later) ---
    # Also signs the JWT that will carry organization_id as a claim once
    # multi-tenancy is wired up in Phase 2/3 (see docs/phase0-architecture-
    # v2-multitenant.md). No tenant logic exists yet in Phase 1 — this is
    # just the same SECRET_KEY slot v1 already had.
    SECRET_KEY: str = "dev-only-placeholder-change-me"

    # --- CORS ---
    # Comma-separated list of allowed frontend origins, e.g.
    # "http://localhost:5173,http://127.0.0.1:5173"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    lru_cache means the .env file is only read once per process instead of
    on every request — settings don't change while the app is running.
    """
    return Settings()


settings = get_settings()
