"""
AI service: wraps calls to the AI provider (Groq by default, Gemini as
an alternative). The API key lives only here, read from environment
variables — it never touches the frontend.
"""
import httpx
from fastapi import HTTPException
from app.config import get_settings
from app.prompts.tool_prompts import get_system_prompt

settings = get_settings()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
)


async def _call_groq(system_prompt: str, user_message: str, history: list[dict]) -> str:
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="AI provider not configured (missing GROQ_API_KEY)")

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(GROQ_URL, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"AI provider error: {e.response.status_code} {e.response.text[:200]}",
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to reach AI provider")

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected AI provider response format")


async def _call_gemini(system_prompt: str, user_message: str, history: list[dict]) -> str:
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="AI provider not configured (missing GEMINI_API_KEY)")

    url = GEMINI_URL_TEMPLATE.format(model=settings.GEMINI_MODEL, key=settings.GEMINI_API_KEY)

    contents = []
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"AI provider error: {e.response.status_code} {e.response.text[:200]}",
            )
        except httpx.RequestError:
            raise HTTPException(status_code=502, detail="Failed to reach AI provider")

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail="Unexpected AI provider response format")


async def generate_ai_reply(
    user_message: str,
    tool_type: str = "general",
    history: list[dict] | None = None,
) -> str:
    """
    Generates an AI reply using the configured provider.
    `history` should be a list of {"role": "user"|"assistant", "content": str}
    representing prior turns in the same chat, oldest first.
    """
    system_prompt = get_system_prompt(tool_type)
    history = history or []

    if settings.AI_PROVIDER == "gemini":
        return await _call_gemini(system_prompt, user_message, history)
    return await _call_groq(system_prompt, user_message, history)
