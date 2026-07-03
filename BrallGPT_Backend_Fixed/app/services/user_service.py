"""
Database logic for the `users` table.
"""
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from app.core.supabase_client import get_supabase
from app.core.security import (
    hash_password,
    verify_password,
    generate_reset_token,
    hash_reset_token,
)

RESET_TOKEN_TTL_MINUTES = 30


def get_user_by_email(email: str) -> dict | None:
    supabase = get_supabase()
    result = supabase.table("users").select("*").eq("email", email.lower()).execute()
    return result.data[0] if result.data else None


def create_user(full_name: str, email: str, password: str) -> dict:
    supabase = get_supabase()

    if get_user_by_email(email):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    new_user = {
        "full_name": full_name,
        "email": email.lower(),
        "password_hash": hash_password(password),
        "is_admin": False,
    }
    result = supabase.table("users").insert(new_user).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create user")

    return result.data[0]


def authenticate_user(email: str, password: str) -> dict:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return user


def update_profile(user_id: str, updates: dict) -> dict:
    supabase = get_supabase()
    clean_updates = {k: v for k, v in updates.items() if v is not None}
    if not clean_updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = supabase.table("users").update(clean_updates).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")
    return result.data[0]


def public_user(user: dict) -> dict:
    """Strips sensitive fields before returning a user to the client."""
    return {
        "id": user["id"],
        "full_name": user.get("full_name"),
        "email": user.get("email"),
        "bio": user.get("bio"),
        "university": user.get("university"),
        "is_admin": user.get("is_admin", False),
        "plan": user.get("plan", "free"),
        "daily_questions_used": user.get("daily_questions_used", 0),
        "created_at": user.get("created_at"),
    }


# ---------- Password reset ----------

def request_password_reset(email: str) -> str | None:
    """
    Creates a password-reset token for the given email, if an account
    exists for it. Always call this the same way regardless of the
    result, and never reveal to the caller whether the email exists —
    that's handled in the router, which always returns a generic message.

    Returns the RAW token (only ever shown once) so the caller can email
    it / return it in dev mode, or None if no account matches.
    """
    user = get_user_by_email(email)
    if not user:
        return None

    supabase = get_supabase()
    raw_token = generate_reset_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)).isoformat()

    supabase.table("password_reset_tokens").insert({
        "user_id": user["id"],
        "token_hash": hash_reset_token(raw_token),
        "expires_at": expires_at,
        "used": False,
    }).execute()

    return raw_token


def reset_password(raw_token: str, new_password: str) -> None:
    """Validates a reset token and updates the user's password."""
    supabase = get_supabase()
    token_hash = hash_reset_token(raw_token)

    result = (
        supabase.table("password_reset_tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .eq("used", False)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    record = result.data[0]
    expires_at = record.get("expires_at")
    if expires_at:
        expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expiry:
            raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    supabase.table("users").update({
        "password_hash": hash_password(new_password),
    }).eq("id", record["user_id"]).execute()

    supabase.table("password_reset_tokens").update({"used": True}).eq("id", record["id"]).execute()
