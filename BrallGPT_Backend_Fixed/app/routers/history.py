from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.services import chat_service

router = APIRouter(prefix="/api/chats", tags=["Chats"])


@router.get("")
async def get_chats(current_user: dict = Depends(get_current_user)):
    chats = chat_service.list_chats(current_user["id"])
    return {"chats": chats}


@router.get("/{chat_id}/messages")
async def get_chat_messages(chat_id: str, current_user: dict = Depends(get_current_user)):
    messages = chat_service.list_messages(chat_id, current_user["id"])
    return {"messages": messages}


@router.delete("/{chat_id}")
async def remove_chat(chat_id: str, current_user: dict = Depends(get_current_user)):
    chat_service.delete_chat(chat_id, current_user["id"])
    return {"status": "deleted", "chat_id": chat_id}
