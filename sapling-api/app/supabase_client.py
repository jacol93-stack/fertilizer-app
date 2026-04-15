from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings


@lru_cache
def get_supabase_admin() -> Client:
    """Supabase client with service_role key — bypasses RLS."""
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


def get_supabase_for_user(access_token: str) -> Client:
    """Supabase client authenticated as a specific user (respects RLS)."""
    s = get_settings()
    client = create_client(s.supabase_url, s.supabase_anon_key)
    client.auth.set_session(access_token, "")
    return client
