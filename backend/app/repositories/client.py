from supabase import Client, create_client

from app.core.config import get_settings


def get_supabase() -> Client:
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_key,
    )

supabase = get_supabase()

