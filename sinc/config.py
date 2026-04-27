from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Banco de dados
    database_url: str = "postgresql+asyncpg://sinc:sinc@localhost:5432/sinc"
    database_sync_url: str = "postgresql+psycopg2://sinc:sinc@localhost:5432/sinc"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT / Auth
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Ambiente
    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
