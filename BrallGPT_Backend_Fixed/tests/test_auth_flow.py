"""
Verifies the full authentication flow end-to-end against the real
FastAPI app, using FakeSupabase in place of the network Supabase client.
Run: python3 tests/test_auth_flow.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "fake-key")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-for-verification-only")
os.environ.setdefault("GROQ_API_KEY", "fake-groq-key")
os.environ.setdefault("ADMIN_EMAILS", "admin@brallgpt.com")

from fastapi.testclient import TestClient
from tests.fake_supabase import FakeSupabase

fake_db = FakeSupabase()

import app.core.supabase_client as supabase_module
supabase_module._supabase_client = fake_db
supabase_module.get_supabase = lambda: fake_db

import app.services.user_service as user_service
import app.core.deps as deps
import app.routers.admin as admin_router
user_service.get_supabase = lambda: fake_db
deps.get_supabase = lambda: fake_db
admin_router.get_supabase = lambda: fake_db

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


print("\n1. SIGNUP")
r = client.post("/api/auth/signup", json={
    "full_name": "Arslan Shan",
    "email": "arslan@example.com",
    "password": "secret123",
})
check("signup returns 201", r.status_code == 201)
body = r.json()
check("signup returns access_token", "access_token" in body)
check("signup response never includes password_hash", "password_hash" not in body["user"])
check("signup user email matches", body["user"]["email"] == "arslan@example.com")
token = body["access_token"]

print("\n2. DUPLICATE SIGNUP REJECTED")
r2 = client.post("/api/auth/signup", json={
    "full_name": "Arslan Again",
    "email": "arslan@example.com",
    "password": "different123",
})
check("duplicate signup returns 409", r2.status_code == 409)

print("\n3. LOGIN")
r3 = client.post("/api/auth/login", json={"email": "arslan@example.com", "password": "secret123"})
check("correct password login returns 200", r3.status_code == 200)
check("login returns a token", "access_token" in r3.json())

r4 = client.post("/api/auth/login", json={"email": "arslan@example.com", "password": "wrongpassword"})
check("wrong password login returns 401", r4.status_code == 401)

r5 = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever"})
check("nonexistent user login returns 401", r5.status_code == 401)

print("\n4. PROTECTED ROUTE ENFORCEMENT")
r6 = client.get("/api/auth/me")
check("no token -> 401", r6.status_code == 401)

r7 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
check("valid token -> 200", r7.status_code == 200)
check("me returns correct email", r7.json()["email"] == "arslan@example.com")

r8 = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage.invalid.token"})
check("garbage token -> 401", r8.status_code == 401)

print("\n5. ADMIN GATING")
r9 = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
check("non-admin blocked from /api/admin/stats -> 403", r9.status_code == 403)

signup_admin = client.post("/api/auth/signup", json={
    "full_name": "Admin User",
    "email": "admin@brallgpt.com",
    "password": "adminpass123",
})
admin_token = signup_admin.json()["access_token"]
r10 = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
check("email in ADMIN_EMAILS -> 200 on /api/admin/stats", r10.status_code == 200)
check("stats reports 2 users", r10.json()["users"] == 2)

print("\n6. PASSWORD IS ACTUALLY HASHED, NOT STORED PLAINTEXT")
stored_user = fake_db.store["users"][0]
check("password_hash is not the plaintext password", stored_user["password_hash"] != "secret123")
check("password_hash looks like a bcrypt hash", stored_user["password_hash"].startswith("$2b$"))

print("\n7. PROFILE UPDATE")
r11 = client.put(
    "/api/profile",
    headers={"Authorization": f"Bearer {token}"},
    json={"bio": "Full-stack dev at UMT", "university": "UMT Lahore"},
)
check("profile update returns 200", r11.status_code == 200)
check("bio was updated", r11.json()["bio"] == "Full-stack dev at UMT")

print(f"\n{'='*50}\n{passed} passed, {failed} failed\n{'='*50}")
sys.exit(1 if failed else 0)
