from fastapi import APIRouter, Depends
from app.models.schemas import ProfileUpdateRequest, FeedbackRequest
from app.core.deps import get_current_user
from app.services import user_service
from app.core.supabase_client import get_supabase

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return user_service.public_user(current_user)


@router.put("")
async def update_profile(payload: ProfileUpdateRequest, current_user: dict = Depends(get_current_user)):
    updated = user_service.update_profile(current_user["id"], payload.model_dump())
    return user_service.public_user(updated)


@router.post("/feedback", status_code=201)
async def submit_feedback(payload: FeedbackRequest, current_user: dict = Depends(get_current_user)):
    supabase = get_supabase()
    result = supabase.table("feedback").insert({
        "user_id": current_user["id"],
        "message": payload.message,
        "rating": payload.rating,
    }).execute()
    return {"status": "received", "feedback": result.data[0] if result.data else None}
