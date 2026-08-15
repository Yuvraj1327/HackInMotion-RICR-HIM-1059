"""
Application configuration, loaded from environment variables (.env in dev).
"""
from functools import lru_cache
from typing import List, Optional

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
    #
    # IMPORTANT for production: this must contain the EXACT origin your
    # frontend is actually served from (scheme + host, no trailing
    # slash) - e.g. https://your-app.vercel.app. A mismatch here is the
    # single most common cause of "Unable to connect to the StockPilot
    # server" / CORS errors in the browser console once both services
    # are deployed, since the browser blocks the response client-side
    # before it ever reaches application code - the backend itself can
    # be perfectly healthy and this will still fail.
    FRONTEND_URL: str = "http://localhost:5173,http://localhost:5174,http://localhost:5175"

    # Optional regex for additional allowed origins, e.g. to cover every
    # preview deployment of a Vercel/Netlify project without having to
    # add each generated URL to FRONTEND_URL by hand. Left empty by
    # default (no extra origins allowed). Example for a Vercel project
    # named "my-app" (covers the production alias AND every preview
    # deployment like my-app-<hash>-<team>.vercel.app):
    #   FRONTEND_URL_REGEX=^https://my-app(-[a-z0-9-]+)?\.vercel\.app$
    FRONTEND_URL_REGEX: str = ""

    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "StockPilot AI"
    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        # Trailing slashes are stripped defensively: browsers NEVER send
        # a trailing slash in the `Origin` header, but pasting a URL
        # straight from the address bar (which often does have one) is
        # an easy mistake to make when setting FRONTEND_URL - and it
        # silently causes the exact same persistent CORS failure as not
        # setting the variable at all, since "https://app.com/" and
        # "https://app.com" are different strings for an exact-match
        # comparison.
        return [origin.strip().rstrip("/") for origin in self.FRONTEND_URL.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> Optional[str]:
        return self.FRONTEND_URL_REGEX.strip() or None

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()