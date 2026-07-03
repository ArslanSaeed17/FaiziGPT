from fastapi import APIRouter, Depends
from app.core.deps import get_current_admin
from app.core.supabase_client import get_supabase

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats")
async def get_stats(admin: dict = Depends(get_current_admin)):
    supabase = get_supabase()

    users_count = supabase.table("users").select("id", count="exact").execute().count or 0
    chats_count = supabase.table("chats").select("id", count="exact").execute().count or 0
    messages_count = supabase.table("messages").select("id", count="exact").execute().count or 0
    feedback_count = supabase.table("feedback").select("id", count="exact").execute().count or 0

    return {
        "users": users_count,
        "chats": chats_count,
        "messages": messages_count,
        "feedback": feedback_count,
    }


@router.get("/users")
async def list_users(admin: dict = Depends(get_current_admin), limit: int = 100):
    supabase = get_supabase()
    result = (
        supabase.table("users")
        .select("id, full_name, email, is_admin, created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"users": result.data or []}


@router.get("/chats")
async def list_all_chats(admin: dict = Depends(get_current_admin), limit: int = 100):
    supabase = get_supabase()
    result = (
        supabase.table("chats")
        .select("id, user_id, title, tool_type, created_at, updated_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"chats": result.data or []}


@router.get("/feedback")
async def list_feedback(admin: dict = Depends(get_current_admin), limit: int = 100):
    supabase = get_supabase()
    result = (
        supabase.table("feedback")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"feedback": result.data or []}
