from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta
from backend.app.core.db import get_session
from backend.app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from backend.app.core.config import settings
from backend.app.models.models import User
from backend.app.schemas.schemas import (
    UserCreate, UserLogin, Token, UserPublic, ForgotPassword, 
    ResetPassword, VerifyOTP, RefreshTokenRequest, UserUpdate, SecurityUpdate
)
from backend.app.api.deps import get_current_user
from jose import jwt, JWTError
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

router = APIRouter()

conf = ConnectionConfig(
    MAIL_USERNAME = settings.SMTP_USER,
    MAIL_PASSWORD = settings.SMTP_PASSWORD,
    MAIL_FROM = settings.EMAILS_FROM_EMAIL,
    MAIL_PORT = settings.SMTP_PORT,
    MAIL_SERVER = settings.SMTP_HOST,
    MAIL_FROM_NAME = settings.PROJECT_NAME,
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

import random

async def send_reset_otp_email(email: str, otp: str):
    html = f"""
    <html>
        <body style="font-family: 'Inter', sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #00A693;">Mã xác thực DocuMind</h2>
                <p>Chào bạn,</p>
                <p>Chúng tôi nhận được yêu cầu khôi phục mật khẩu cho tài khoản của bạn.</p>
                <p>Mã xác thực (OTP) của bạn là:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <span style="font-size: 36px; font-weight: bold; color: #00A693; letter-spacing: 10px;">{otp}</span>
                </div>
                <p>Mã này có hiệu lực trong 5 phút. Vui lòng không chia sẻ mã này với bất kỳ ai.</p>
                <p>Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 12px; color: #999;">Trân trọng,<br>Đội ngũ DocuMind</p>
            </div>
        </body>
    </html>
    """
    
    message = MessageSchema(
        subject="Mã xác thực khôi phục mật khẩu DocuMind",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="ERR_EMAIL_TAKEN"
        )
    
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password)
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    access_token = create_access_token(str(db_user.user_id))
    refresh_token = create_refresh_token(str(db_user.user_id))
    
    db_user.refresh_token = refresh_token
    db_user.refresh_token_expiry = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session.add(db_user)
    session.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "full_name": db_user.full_name,
        "avatar_id": db_user.avatar_id
    }

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ERR_INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.user_id)
    refresh_token = create_refresh_token(subject=user.user_id)
    
    user.refresh_token = refresh_token
    user.refresh_token_expiry = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session.add(user)
    session.commit()
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "full_name": user.full_name,
        "avatar_id": user.avatar_id
    }

@router.post("/refresh-token", response_model=Token)
def refresh_token(data: RefreshTokenRequest, session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(data.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="ERR_TOKEN_INVALID")
    except JWTError:
        raise HTTPException(status_code=401, detail="ERR_TOKEN_EXPIRED")
    
    user = session.get(User, user_id)
    if not user or user.refresh_token != data.refresh_token or user.refresh_token_expiry < datetime.utcnow():
        raise HTTPException(status_code=401, detail="ERR_SESSION_EXPIRED")
    
    # Tạo cặp token mới
    new_access = create_access_token(subject=user.user_id)
    new_refresh = create_refresh_token(subject=user.user_id)
    
    user.refresh_token = new_refresh
    user.refresh_token_expiry = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session.add(user)
    session.commit()
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "full_name": user.full_name,
        "avatar_id": user.avatar_id
    }

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    current_user.refresh_token = None
    current_user.refresh_token_expiry = None
    session.add(current_user)
    session.commit()
    return {"message": "MSG_LOGOUT_SUCCESS"}

@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="ERR_EMAIL_NOT_FOUND"
        )
    
    otp = f"{random.randint(100000, 999999)}"
    user.otp_code = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    
    session.add(user)
    session.commit()
    
    await send_reset_otp_email(data.email, otp)
    return {"message": "MSG_OTP_SENT"}

@router.post("/verify-otp")
def verify_otp(data: VerifyOTP, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or user.otp_code != data.otp_code:
        raise HTTPException(status_code=400, detail="ERR_OTP_INVALID")
    
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="ERR_OTP_EXPIRED")
    
    reset_token = create_access_token(
        subject=str(user.user_id), expires_delta=timedelta(minutes=10)
    )
    user.otp_code = None
    user.otp_expiry = None
    session.add(user)
    session.commit()
    return {"reset_token": reset_token}

@router.post("/reset-password")
def reset_password(data: ResetPassword, session: Session = Depends(get_session)):
    try:
        payload = jwt.decode(data.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=400, detail="ERR_TOKEN_INVALID")
    except JWTError:
        raise HTTPException(status_code=400, detail="ERR_TOKEN_EXPIRED")
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ERR_USER_NOT_FOUND")
    
    user.hashed_password = get_password_hash(data.new_password)
    access_token = create_access_token(subject=str(user.user_id))
    refresh_token = create_refresh_token(subject=str(user.user_id))
    
    user.refresh_token = refresh_token
    user.refresh_token_expiry = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session.add(user)
    session.commit()
    session.refresh(user)

    return {
        "message": "MSG_PASSWORD_RESET_SUCCESS",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "full_name": user.full_name,
        "avatar_id": user.avatar_id
    }

@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserPublic)
def update_user_me(data: UserUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.avatar_id is not None:
        current_user.avatar_id = data.avatar_id
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@router.put("/security", response_model=UserPublic)
def update_security(data: SecurityUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    if data.old_password and data.new_password:
        if not verify_password(data.old_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="ERR_OLD_PASSWORD_INCORRECT")
        current_user.hashed_password = get_password_hash(data.new_password)
        
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user
