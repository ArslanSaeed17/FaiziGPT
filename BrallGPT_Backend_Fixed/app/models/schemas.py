"""
Pydantic models for request validation and response shaping.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ---------- Auth ----------

class SignupRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, max_length=128)


# ---------- Chat ----------

class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    chat_id: Optional[str] = None  # if None, a new chat is created


class ToolChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    tool_type: str  # study | code | cyber | business | resume | project | career
    chat_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    chat_id: str
    reply: str
    created_at: datetime
    daily_questions_used: Optional[int] = None


# ---------- History ----------

class ChatSummary(BaseModel):
    id: str
    title: str
    tool_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


# ---------- Profile ----------

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    university: Optional[str] = None


# ---------- Feedback ----------

class FeedbackRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
