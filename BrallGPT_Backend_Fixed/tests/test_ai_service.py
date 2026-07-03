"""
Verifies app/services/ai_service.py in isolation using respx to mock the
Groq and Gemini HTTP endpoints. This sandbox has no network route to
api.groq.com or generativelanguage.googleapis.com, so this is how the
request/response contract, tool-prompt selection, and error handling are
proven correct before you plug in a real API key.

Run: python3 tests/test_ai_service.py
"""
import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-verification-only")
os.environ.setdefault("GROQ_API_KEY", "fake-groq-key")

import respx
import httpx
from fastapi import HTTPException

passed = 0
failed = 0


def check(label, condition):
    global passed, failed
    if condition:
        print(f"  PASS  {label}")
        passed += 1
    else:
        print(f"  FAIL  {label}")
        failed += 1


async def main():
    global passed, failed

    # Reload config/service fresh so env vars above take effect
    from app.config import get_settings
    get_settings.cache_clear()
    import importlib
    import app.services.ai_service as ai_service
    importlib.reload(ai_service)
    from app.prompts.tool_prompts import get_system_prompt

    # ---------------------------------------------------------------
    print("\n1. GROQ — successful reply, correct system prompt per tool")
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(
                200,
                json={"choices": [{"message": {"content": "Here is your MIPS explanation..."}}]},
            )
        )
        reply = await ai_service.generate_ai_reply("Explain MIPS branching", tool_type="study")
        check("returns model's text content", reply == "Here is your MIPS explanation...")

        sent_body = route.calls[0].request.content
        import json as _json
        payload = _json.loads(sent_body)
        check("uses configured Groq model", payload["model"] == ai_service.settings.GROQ_MODEL)
        check(
            "system prompt matches StudyGPT persona",
            payload["messages"][0]["content"] == get_system_prompt("study"),
        )
        check(
            "user message is the last message",
            payload["messages"][-1] == {"role": "user", "content": "Explain MIPS branching"},
        )
        check(
            "Authorization header carries the API key",
            route.calls[0].request.headers["authorization"] == f"Bearer {ai_service.settings.GROQ_API_KEY}",
        )

    # ---------------------------------------------------------------
    print("\n2. GROQ — conversation history is threaded correctly")
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Follow-up answer"}}]})
        )
        history = [
            {"role": "user", "content": "What is a stack overflow vuln?"},
            {"role": "assistant", "content": "It happens when..."},
        ]
        await ai_service.generate_ai_reply("Give me a CTF example", tool_type="cyber", history=history)
        payload = _json.loads(route.calls[0].request.content)
        check("history messages appear between system and new user msg", len(payload["messages"]) == 4)
        check("history order preserved", payload["messages"][1]["content"] == "What is a stack overflow vuln?")
        check("new user message appended last", payload["messages"][3]["content"] == "Give me a CTF example")

    # ---------------------------------------------------------------
    print("\n3. GROQ — provider error (bad API key) surfaces as HTTP 502, not a crash")
    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(401, json={"error": {"message": "invalid_api_key"}})
        )
        try:
            await ai_service.generate_ai_reply("test", tool_type="general")
            check("raises HTTPException on provider auth error", False)
        except HTTPException as e:
            check("raises HTTPException on provider auth error", e.status_code == 502)

    # ---------------------------------------------------------------
    print("\n4. GROQ — malformed provider response handled gracefully")
    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"unexpected": "shape"})
        )
        try:
            await ai_service.generate_ai_reply("test", tool_type="general")
            check("malformed response raises HTTPException", False)
        except HTTPException as e:
            check("malformed response raises HTTPException", e.status_code == 502)

    # ---------------------------------------------------------------
    print("\n5. GROQ — network failure (timeout/DNS) handled gracefully")
    with respx.mock(assert_all_called=True) as mock:
        mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
            side_effect=httpx.ConnectError("connection refused")
        )
        try:
            await ai_service.generate_ai_reply("test", tool_type="general")
            check("network error raises HTTPException", False)
        except HTTPException as e:
            check("network error raises HTTPException", e.status_code == 502)

    # ---------------------------------------------------------------
    print("\n6. Missing API key fails fast with a clear config error")
    ai_service.settings.GROQ_API_KEY = ""
    try:
        await ai_service.generate_ai_reply("test", tool_type="general")
        check("missing key raises HTTPException", False)
    except HTTPException as e:
        check("missing key raises HTTPException", e.status_code == 500)
    ai_service.settings.GROQ_API_KEY = "fake-groq-key"  # restore

    # ---------------------------------------------------------------
    print("\n7. GEMINI — successful reply via alternate provider")
    ai_service.settings.AI_PROVIDER = "gemini"
    ai_service.settings.GEMINI_API_KEY = "fake-gemini-key"
    with respx.mock(assert_all_called=True) as mock:
        route = mock.post(
            url__regex=r"https://generativelanguage\.googleapis\.com/.*"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "Gemini says hi"}]}}]},
            )
        )
        reply = await ai_service.generate_ai_reply("hello", tool_type="general")
        check("Gemini path returns correct text", reply == "Gemini says hi")
    ai_service.settings.AI_PROVIDER = "groq"  # restore

    # ---------------------------------------------------------------
    print("\n8. Every tool type maps to a distinct, non-generic system prompt")
    tool_types = ["study", "code", "cyber", "business", "resume", "project", "career"]
    prompts = {t: get_system_prompt(t) for t in tool_types}
    check("all 7 tool prompts are unique", len(set(prompts.values())) == 7)
    check("unknown tool_type falls back to general prompt", get_system_prompt("nonsense") == get_system_prompt("general"))
    check(
        "CyberGPT prompt explicitly restricts to authorized/ethical use",
        "authorized" in prompts["cyber"].lower() and "unauthorized" in prompts["cyber"].lower(),
    )

    print(f"\n{'='*50}\n{passed} passed, {failed} failed\n{'='*50}")
    return failed


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(1 if result else 0)
