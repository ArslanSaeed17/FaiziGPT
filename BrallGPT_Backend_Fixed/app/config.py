"""
Application configuration.
Loads all settings from environment variables (.env in local dev,
Railway environment variables in production). Never hardcode secrets here.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "BrallGPT API"
    ENVIRONMENT: str = "development"  # development | production

    # --- CORS ---
    # Comma-separated list of allowed frontend origins
    ALLOWED_ORIGINS: str = http://localhost:5500,http://127.0.0.1:5500"

    # --- Supabase ---
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str  # server-side only, never exposed to frontend

    # --- JWT Auth ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # --- AI Provider ---
    AI_PROVIDER: str = "groq"  # "groq" or "gemini"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # --- Admin ---
    ADMIN_EMAILS: str = ""  # comma-separated emails treated as admin

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def admin_emails_list(self) -> list[str]:
        return [e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
