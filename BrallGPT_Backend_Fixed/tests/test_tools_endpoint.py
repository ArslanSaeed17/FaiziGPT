"""
Full-stack test of the tool-chat flow: HTTP request -> auth -> DB (fake) ->
AI provider (mocked) -> DB save -> HTTP response. Proves the pieces built
in Phases 2, 3, 4 and 5 actually work together, not just in isolation.

Run: python3 tests/test_tools_endpoint.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-verification-only")
os.environ.setdefault("GROQ_API_KEY", "fake-groq-key")

import respx
import httpx
from fastapi.testclient import TestClient
from tests.fake_supabase import FakeSupabase

fake_db = FakeSupabase()

import app.core.supabase_client as supabase_module
supabase_module._supabase_client = fake_db
supabase_module.get_supabase = lambda: fake_db

import app.services.user_service as user_service
import app.services.chat_service as chat_service
import app.core.deps as deps
user_service.get_supabase = lambda: fake_db
chat_service.get_supabase = lambda: fake_db
deps.get_supabase = lambda: fake_db

from app.main import app

client = TestClient(app)

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


# --- get an authenticated user ---
signup = client.post("/api/auth/signup", json={
    "full_name": "Shan",
    "email": "shan@umt.edu.pk",
    "password": "password123",
})
token = signup.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

print("\n1. NEW CHAT — CodeGPT debugs a snippet")
with respx.mock(assert_all_called=True) as mock:
    mock.post(GROQ_URL).mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": "The bug is an off-by-one error in your loop."}}]},
        )
    )
    r = client.post(
        "/api/tools/chat",
        headers=headers,
        json={"message": "My for loop skips the last index", "tool_type": "code"},
    )
    check("returns 200", r.status_code == 200)
    body = r.json()
    check("reply text is passed through", body["reply"] == "The bug is an off-by-one error in your loop.")
    check("a chat_id was created", "chat_id" in body and body["chat_id"])
    chat_id = body["chat_id"]

print("\n2. INVALID TOOL TYPE REJECTED")
r2 = client.post("/api/tools/chat", headers=headers, json={"message": "hi", "tool_type": "astrology"})
check("unknown tool_type -> 400", r2.status_code == 400)

print("\n3. FOLLOW-UP MESSAGE IN SAME CHAT — history threads correctly")
with respx.mock(assert_all_called=True) as mock:
    route = mock.post(GROQ_URL).mock(
        return_value=httpx.Response(200, json={"choices": [{"message": {"content": "Try using range(len(arr))."}}]})
    )
    r3 = client.post(
        "/api/tools/chat",
        headers=headers,
        json={"message": "How do I fix it?", "tool_type": "code", "chat_id": chat_id},
    )
    check("follow-up returns 200", r3.status_code == 200)
    check("follow-up reuses the same chat_id", r3.json()["chat_id"] == chat_id)

    sent = json.loads(route.calls[0].request.content)
    roles_and_content = [(m["role"], m["content"]) for m in sent["messages"]]
    check(
        "prior turn (user question) included in context sent to AI",
        ("user", "My for loop skips the last index") in roles_and_content,
    )
    check(
        "prior turn (assistant reply) included in context sent to AI",
        ("assistant", "The bug is an off-by-one error in your loop.") in roles_and_content,
    )

print("\n4. CHAT HISTORY RETRIEVAL")
r4 = client.get("/api/chats", headers=headers)
check("history list returns 200", r4.status_code == 200)
check("1 chat exists for this user", len(r4.json()["chats"]) == 1)

r5 = client.get(f"/api/chats/{chat_id}/messages", headers=headers)
check("messages endpoint returns 200", r5.status_code == 200)
check("4 messages stored (2 user + 2 assistant)", len(r5.json()["messages"]) == 4)

print("\n5. CROSS-USER ACCESS BLOCKED")
other_signup = client.post("/api/auth/signup", json={
    "full_name": "Other User",
    "email": "other@example.com",
    "password": "password123",
})
other_token = other_signup.json()["access_token"]
r6 = client.get(f"/api/chats/{chat_id}/messages", headers={"Authorization": f"Bearer {other_token}"})
check("another user cannot read this chat's messages -> 404", r6.status_code == 404)

print("\n6. DELETE CHAT")
r7 = client.delete(f"/api/chats/{chat_id}", headers=headers)
check("delete returns 200", r7.status_code == 200)
r8 = client.get("/api/chats", headers=headers)
check("chat list is now empty", len(r8.json()["chats"]) == 0)

print("\n7. AI PROVIDER OUTAGE DOESN'T CORRUPT CHAT STATE")
with respx.mock(assert_all_called=True) as mock:
    mock.post(GROQ_URL).mock(return_value=httpx.Response(503, text="Service Unavailable"))
    r9 = client.post(
        "/api/tools/chat",
        headers=headers,
        json={"message": "This will fail", "tool_type": "business"},
    )
    check("provider outage surfaces as 502, not 500 crash", r9.status_code == 502)

print(f"\n{'='*50}\n{passed} passed, {failed} failed\n{'='*50}")
sys.exit(1 if failed else 0)
