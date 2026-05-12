from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta
from backend.app.core.db import get_session
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.config import settings
from backend.app.models.models import User
from backend.app.schemas.schemas import UserCreate, UserLogin, Token, UserPublic, ForgotPassword, ResetPassword, VerifyOTP
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
    # ... (giữ nguyên logic register)
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email này đã được sử dụng."
        )
    
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password)
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        str(db_user.user_id), expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "full_name": db_user.full_name
    }

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.user_id)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "full_name": user.full_name
    }

@router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="Email này chưa được đăng ký trong hệ thống."
        )
    
    # Tạo mã OTP 6 số
    otp = f"{random.randint(100000, 999999)}"
    user.otp_code = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=5)
    
    session.add(user)
    session.commit()
    
    # Gửi email chứa OTP
    await send_reset_otp_email(data.email, otp)
    
    return {"message": "Mã xác thực đã được gửi vào email của bạn."}

@router.post("/verify-otp")
def verify_otp(data: VerifyOTP, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    if not user or user.otp_code != data.otp_code:
        raise HTTPException(status_code=400, detail="Mã xác thực không chính xác.")
    
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="Mã xác thực đã hết hạn.")
    
    # Mã đúng -> Tạo token tạm thời để đặt lại mật khẩu (hết hạn sau 10 phút)
    reset_token = create_access_token(
        subject=str(user.user_id), expires_delta=timedelta(minutes=10)
    )
    
    # Xóa OTP sau khi dùng xong
    user.otp_code = None
    user.otp_expiry = None
    session.add(user)
    session.commit()
    
    return {"reset_token": reset_token}

@router.post("/reset-password")
def reset_password(data: ResetPassword, session: Session = Depends(get_session)):
    # Giải mã token để lấy user_id
    try:
        payload = jwt.decode(data.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=400, detail="Token không hợp lệ.")
    except JWTError:
        raise HTTPException(status_code=400, detail="Token đã hết hạn hoặc không hợp lệ.")
    
    # Tìm user và cập nhật mật khẩu
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
    
    # Cập nhật mật khẩu mới
    user.hashed_password = get_password_hash(data.new_password)
    session.add(user)
    session.commit()
    session.refresh(user)

    # Tạo token đăng nhập mới
    access_token = create_access_token(subject=str(user.user_id))

    return {
        "message": "Mật khẩu của bạn đã được cập nhật thành công!",
        "access_token": access_token,
        "full_name": user.full_name
    }

@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user
