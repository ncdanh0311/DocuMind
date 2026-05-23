from typing import Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    full_name: Optional[str] = None
    avatar_id: Optional[str] = None

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserPublic(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    avatar_id: Optional[str] = None

    class Config:
        from_attributes = True

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str

class VerifyOTP(BaseModel):
    email: EmailStr
    otp_code: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_id: Optional[str] = None

class SecurityUpdate(BaseModel):
    old_password: Optional[str] = None
    new_password: Optional[str] = None

class DocumentChunkResponse(BaseModel):
    docuchunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    page_number: Optional[int] = None

    class Config:
        from_attributes = True

class NotificationResponse(BaseModel):
    notification_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    body: str
    is_read: bool
    type: str
    created_at: datetime

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    question: str

class CitationResponse(BaseModel):
    id: int
    source_title: str
    page_number: Optional[int] = None
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    citations: list[CitationResponse] = []


