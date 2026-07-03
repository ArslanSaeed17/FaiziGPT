"""
Reusable FastAPI dependencies for authentication and authorization.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.core.supabase_client import get_supabase
from app.config import get_settings

settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """
    Validates the JWT from the Authorization header and returns the
    corresponding user row from Supabase. Raises 401 if invalid/missing.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_access_token(credentials.credentials)
    if payload is None or "user_id" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    supabase = get_supabase()
    result = supabase.table("users").select("*").eq("id", payload["user_id"]).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return result.data[0]


async def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    """
    Ensures the current user is an admin. Admin status is determined by
    the `is_admin` flag on the users table (set manually in Supabase,
    or auto-granted to emails listed in ADMIN_EMAILS).
    """
    is_admin = user.get("is_admin", False)
    if not is_admin and user.get("email", "").lower() not in settings.admin_emails_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
