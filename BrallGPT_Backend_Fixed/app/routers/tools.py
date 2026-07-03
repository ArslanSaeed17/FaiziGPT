from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ToolChatRequest, ChatMessageResponse
from app.core.deps import get_current_user
from app.services import chat_service
from app.services.ai_service import generate_ai_reply
from app.prompts.tool_prompts import TOOL_SYSTEM_PROMPTS

router = APIRouter(prefix="/api/tools", tags=["AI Tools"])

VALID_TOOLS = set(TOOL_SYSTEM_PROMPTS.keys()) - {"general"}


@router.get("")
async def list_tools():
    """Returns metadata for all available AI tools, used to render the tools grid."""
    return {
        "tools": [
            {"id": "study", "name": "StudyGPT", "description": "Assignments, notes, MCQs, exam prep"},
            {"id": "code", "name": "CodeGPT", "description": "Programming help and debugging"},
            {"id": "cyber", "name": "CyberGPT", "description": "Ethical cybersecurity, Kali/Linux, CTF guidance"},
            {"id": "business", "name": "BusinessGPT", "description": "Business ideas, marketing, startup roadmap"},
            {"id": "resume", "name": "ResumeGPT", "description": "CV, resume, LinkedIn, cover letters"},
            {"id": "project", "name": "ProjectGPT", "description": "FYP and web/app/AI project ideas"},
            {"id": "career", "name": "CareerGPT", "description": "Roadmaps, interview prep, skill planning"},
        ]
    }


@router.post("/chat", response_model=ChatMessageResponse)
async def tool_chat(payload: ToolChatRequest, current_user: dict = Depends(get_current_user)):
    if payload.tool_type not in VALID_TOOLS:
        raise HTTPException(status_code=400, detail=f"Unknown tool_type. Valid options: {sorted(VALID_TOOLS)}")

    user_id = current_user["id"]

    if payload.chat_id:
        chat_row = chat_service.get_chat(payload.chat_id, user_id)
        history = chat_service.get_recent_history(chat_row["id"])
    else:
        title = payload.message[:60]
        chat_row = chat_service.create_chat(user_id, title, tool_type=payload.tool_type)
        history = []

    chat_service.add_message(chat_row["id"], "user", payload.message)

    reply = await generate_ai_reply(payload.message, tool_type=payload.tool_type, history=history)

    saved_reply = chat_service.add_message(chat_row["id"], "assistant", reply)
    chat_service.touch_chat(chat_row["id"])

    return ChatMessageResponse(
        chat_id=chat_row["id"],
        reply=reply,
        created_at=saved_reply["created_at"],
    )
