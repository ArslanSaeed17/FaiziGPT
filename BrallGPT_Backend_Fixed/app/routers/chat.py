from fastapi import APIRouter, Depends
from app.models.schemas import ChatMessageRequest, ChatMessageResponse
from app.core.deps import get_current_user
from app.services import chat_service, user_service
from app.services.ai_service import generate_ai_reply

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatMessageResponse)
async def chat(payload: ChatMessageRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]

    # Enforce the free-plan daily limit and persist the increment up front,
    # so a page refresh reflects the real usage instead of resetting to 0.
    usage = user_service.increment_daily_usage(user_id, current_user.get("plan", "free"))

    if payload.chat_id:
        chat_row = chat_service.get_chat(payload.chat_id, user_id)
        history = chat_service.get_recent_history(chat_row["id"])
    else:
        title = payload.message[:60]
        chat_row = chat_service.create_chat(user_id, title, tool_type="general")
        history = []

    chat_service.add_message(chat_row["id"], "user", payload.message)

    reply = await generate_ai_reply(payload.message, tool_type="general", history=history)

    saved_reply = chat_service.add_message(chat_row["id"], "assistant", reply)
    chat_service.touch_chat(chat_row["id"])

    return ChatMessageResponse(
        chat_id=chat_row["id"],
        reply=reply,
        created_at=saved_reply["created_at"],
        daily_questions_used=usage,
    )
