from functools import lru_cache
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Smart University CMS API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/smart_university_cms"
    test_database_url: str | None = None
    jwt_secret_key: str = Field("CHANGE_ME_IN_ENVIRONMENT", validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY", "SECRET"))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    frontend_url: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def model_post_init(self, __context):
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        if self.test_database_url and self.test_database_url.startswith("postgresql://"):
            self.test_database_url = self.test_database_url.replace("postgresql://", "postgresql+psycopg://", 1)

@lru_cache
def get_settings() -> Settings: return Settings()
settings=get_settings()
