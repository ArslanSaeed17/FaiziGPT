from fastapi import APIRouter, Depends
from app.config import get_settings
from app.models.schemas import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
)
from app.services import user_service
from app.core.security import create_access_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])
settings = get_settings()


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(payload: SignupRequest):
    user = user_service.create_user(payload.full_name, payload.email, payload.password)
    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    return AuthResponse(access_token=token, user=user_service.public_user(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest):
    user = user_service.authenticate_user(payload.email, payload.password)
    token = create_access_token({"user_id": user["id"], "email": user["email"]})
    return AuthResponse(access_token=token, user=user_service.public_user(user))


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    return user_service.public_user(current_user)


@router.post("/password-reset")
async def password_reset(payload: PasswordResetRequest):
    """
    Requests a password reset link. Always returns the same generic
    message whether or not the email exists, so callers can't use this
    endpoint to discover which emails are registered.
    """
    raw_token = user_service.request_password_reset(payload.email)

    response = {"message": "If an account exists for this email, a reset link has been sent."}

    # No email provider is wired up yet, so in local/dev we surface the
    # raw token directly in the response for testing. Never do this in
    # production — swap this block out once SMTP/Resend/etc. is added.
    if raw_token and settings.ENVIRONMENT != "production":
        response["dev_reset_token"] = raw_token

    return response


@router.post("/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirmRequest):
    """Completes a password reset using the token issued above."""
    user_service.reset_password(payload.token, payload.new_password)
    return {"message": "Password updated. You can now log in with your new password."}
