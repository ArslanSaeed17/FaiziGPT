"""
Supabase client initialization.
Uses the SERVICE ROLE key because all writes/reads are mediated by our
FastAPI backend (backend-issued JWT auth, not native Supabase Auth sessions).
The service role key must NEVER be sent to the frontend.
"""
from supabase import create_client, Client
from app.config import get_settings

settings = get_settings()

_supabase_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client
