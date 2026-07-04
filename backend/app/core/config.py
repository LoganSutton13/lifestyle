from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: Literal["development", "preview", "production"] = "development"
    DATABASE_URL: str
    DB_POOL_MODE: Literal["serverless", "persistent"] = "persistent"
    JWT_SECRET: str
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 30
    CORS_ORIGINS: str = "http://localhost:5173"
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str = ""
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_FIRST_NAME: str = "Admin"
    INITIAL_ADMIN_LAST_NAME: str = "User"
    INITIAL_ADMIN_PASSWORD: str = "ChangeMe12345"

    @model_validator(mode="after")
    def validate_database_url(self) -> "Settings":
        parsed = urlparse(self.DATABASE_URL)
        if parsed.scheme not in {"postgresql", "postgresql+asyncpg", "sqlite+aiosqlite"}:
            msg = "DATABASE_URL must use postgresql+asyncpg:// or sqlite+aiosqlite://"
            raise ValueError(msg)
        if parsed.scheme.startswith("postgresql") and not parsed.username:
            msg = (
                "DATABASE_URL is missing username/password. "
                "Use: postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/fitness_app_dev"
            )
            raise ValueError(msg)
        return self
    DB_POOL_MODE: Literal["serverless", "persistent"] = "persistent"
    JWT_SECRET: str
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 30
    CORS_ORIGINS: str = "http://localhost:5173"
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str = ""
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_FIRST_NAME: str = "Admin"
    INITIAL_ADMIN_LAST_NAME: str = "User"
    INITIAL_ADMIN_PASSWORD: str = "ChangeMe12345"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
