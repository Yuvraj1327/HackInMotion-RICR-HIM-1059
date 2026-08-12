"""
Application configuration, loaded from environment variables (.env in dev).
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # Frontend / CORS
    # Comma-separated list of allowed origins. Vite's dev server defaults
    # to 5173 but auto-increments to the next free port (5174, 5175, ...)
    # if 5173 is already taken, so the local-dev default covers that
    # small range out of the box. Override via .env for anything else
    # (a fixed port, a deployed frontend URL, etc.).
    FRONTEND_URL: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175"

    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "StockPilot AI"
    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.FRONTEND_URL.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()