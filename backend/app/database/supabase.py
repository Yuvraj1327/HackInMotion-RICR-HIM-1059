"""
Supabase client factory.

Two clients are exposed:

- `get_service_client()`  -> uses the SERVICE ROLE key. Bypasses RLS.
  Used internally by the backend AFTER we have already verified the
  user's JWT ourselves and manually filtered every query by user_id.
  Never expose this client or its key to the frontend.

- `get_anon_client()`     -> uses the ANON key, for operations (like
  auth) that don't need elevated privileges.

Even though the service client bypasses RLS, every repository method in
this codebase still explicitly filters `.eq("user_id", user_id)` on every
query as defense-in-depth, because RLS bypass + a forgotten filter would
otherwise leak data across users.
"""
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_service_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not configured. "
            "Set them in your .env file."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache
def get_anon_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_ANON_KEY not configured. "
            "Set them in your .env file."
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
