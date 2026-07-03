"""
Database logic for `chats` and `messages` tables.
"""
from fastapi import HTTPException
from app.core.supabase_client import get_supabase


def create_chat(user_id: str, title: str, tool_type: str | None = None) -> dict:
    supabase = get_supabase()
    result = supabase.table("chats").insert({
        "user_id": user_id,
        "title": title[:80],
        "tool_type": tool_type,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create chat")
    return result.data[0]


def get_chat(chat_id: str, user_id: str) -> dict:
    supabase = get_supabase()
    result = (
        supabase.table("chats")
        .select("*")
        .eq("id", chat_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Chat not found")
    return result.data[0]


def list_chats(user_id: str) -> list[dict]:
    supabase = get_supabase()
    result = (
        supabase.table("chats")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data or []


def touch_chat(chat_id: str) -> None:
    """Updates the chat's updated_at timestamp after a new message."""
    supabase = get_supabase()
    supabase.table("chats").update({"updated_at": "now()"}).eq("id", chat_id).execute()


def delete_chat(chat_id: str, user_id: str) -> None:
    supabase = get_supabase()
    # Ensure the chat belongs to this user before deleting
    get_chat(chat_id, user_id)
    supabase.table("messages").delete().eq("chat_id", chat_id).execute()
    supabase.table("chats").delete().eq("id", chat_id).execute()


def add_message(chat_id: str, role: str, content: str) -> dict:
    supabase = get_supabase()
    result = supabase.table("messages").insert({
        "chat_id": chat_id,
        "role": role,
        "content": content,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save message")
    return result.data[0]


def list_messages(chat_id: str, user_id: str) -> list[dict]:
    # Verify ownership first
    get_chat(chat_id, user_id)

    supabase = get_supabase()
    result = (
        supabase.table("messages")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []


def get_recent_history(chat_id: str, limit: int = 12) -> list[dict]:
    """Returns the last `limit` messages formatted for the AI provider."""
    supabase = get_supabase()
    result = (
        supabase.table("messages")
        .select("role, content")
        .eq("chat_id", chat_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    messages = result.data or []
    return list(reversed(messages))
