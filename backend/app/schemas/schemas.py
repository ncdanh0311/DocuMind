from typing import Optional
import uuid
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
    biometric_enabled: bool = False
    has_app_pin: bool = False

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
    biometric_enabled: Optional[bool] = None
    app_pin: Optional[str] = None # Nếu "" là tắt mã PIN
    old_password: Optional[str] = None
    new_password: Optional[str] = None
