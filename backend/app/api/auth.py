import hmac
import logging
import secrets
import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from backend.app.core.db import get_session
from backend.app.core.config import settings
from backend.app.core.security import (
    create_token, credential_hash, decode_token, get_password_hash, is_expired, otp_hash, utc_now, verify_password,
)
from backend.app.models.models import AuthSession, PasswordResetChallenge, User
from backend.app.schemas.schemas import (
    UserCreate, UserLogin, Token, UserPublic, ForgotPassword, ResetPassword, VerifyOTP,
    RefreshTokenRequest, UserUpdate, SecurityUpdate, ResetTokenResponse, ResetPasswordResponse, MessageResponse,
)
from backend.app.api.deps import get_current_user, get_current_session
from backend.app.services.auth_service import consume_reset_rate_limit, issue_tokens, lock_user, revoke_user_credentials, same_hash

logger = logging.getLogger(__name__)
router = APIRouter()

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

    conf = ConnectionConfig(
        MAIL_USERNAME=settings.SMTP_USER, MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.EMAILS_FROM_EMAIL, MAIL_PORT=settings.SMTP_PORT,
        MAIL_SERVER=settings.SMTP_HOST, MAIL_FROM_NAME=settings.PROJECT_NAME,
        MAIL_STARTTLS=settings.SMTP_TLS, MAIL_SSL_TLS=settings.SMTP_SSL,
        USE_CREDENTIALS=True, VALIDATE_CERTS=True,
    )
    fm = FastMail(conf)
    await fm.send_message(message)

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    user = User(email=user_in.email, full_name=user_in.full_name, hashed_password=get_password_hash(user_in.password))
    try:
        session.add(user)
        session.flush()
        result = issue_tokens(session, user)
        session.commit()
        return result
    except IntegrityError:
        session.rollback()
        raise HTTPException(400, "ERR_EMAIL_TAKEN") from None

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == user_in.email).with_for_update()).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(401, "ERR_INVALID_CREDENTIALS", headers={"WWW-Authenticate": "Bearer"})
    result = issue_tokens(session, user)
    session.commit()
    return result

@router.post("/refresh-token", response_model=Token)
def refresh_token(data: RefreshTokenRequest, session: Session = Depends(get_session)):
    payload = decode_token(data.refresh_token, "refresh")
    user = lock_user(session, uuid.UUID(payload["sub"]))
    auth_session = session.exec(select(AuthSession).where(AuthSession.session_id == uuid.UUID(payload["sid"])).with_for_update()).first()
    if (not auth_session or auth_session.user_id != user.user_id or auth_session.revoked_at is not None
            or is_expired(auth_session.expires_at) or not same_hash(auth_session.refresh_hash, data.refresh_token)):
        raise HTTPException(401, "ERR_SESSION_EXPIRED")
    result = issue_tokens(session, user, auth_session)
    session.commit()
    return result

@router.post("/logout", response_model=MessageResponse)
def logout(auth_session: AuthSession = Depends(get_current_session), session: Session = Depends(get_session)):
    lock_user(session, auth_session.user_id)
    auth_session.revoked_at = utc_now()
    session.add(auth_session)
    session.commit()
    return {"message": "MSG_LOGOUT_SUCCESS"}

@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPassword, request: Request, session: Session = Depends(get_session)):
    # Never trust a caller-supplied forwarding header for IP-based limits.
    ip = request.client.host if request.client else "unknown"
    allowed = consume_reset_rate_limit(session, data.email, ip)
    user = session.exec(select(User).where(User.email == data.email).with_for_update()).first() if allowed else None
    code = None
    if user:
        now = utc_now()
        for previous in session.exec(select(PasswordResetChallenge).where(PasswordResetChallenge.user_id == user.user_id, PasswordResetChallenge.used_at.is_(None))).all():
            previous.used_at = now
            session.add(previous)
        code = f"{secrets.randbelow(1000000):06d}"
        challenge = PasswordResetChallenge(user_id=user.user_id, otp_hash="", otp_expires_at=now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES))
        challenge.otp_hash = otp_hash(challenge.challenge_id, code)
        session.add(challenge)
    session.commit()
    if code is not None:
        try:
            await send_reset_otp_email(data.email, code)
        except Exception:
            # Do not expose provider details or distinguish registered addresses.
            logger.warning("Password reset delivery failed")
    return {"message": "MSG_OTP_SENT"}

@router.post("/verify-otp", response_model=ResetTokenResponse)
def verify_otp(data: VerifyOTP, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email).with_for_update()).first()
    challenge = None
    if user:
        challenge = session.exec(select(PasswordResetChallenge).where(
            PasswordResetChallenge.user_id == user.user_id, PasswordResetChallenge.used_at.is_(None),
            PasswordResetChallenge.otp_consumed_at.is_(None),
        ).order_by(PasswordResetChallenge.created_at.desc()).with_for_update()).first()
    if not challenge or challenge.attempts >= settings.OTP_MAX_ATTEMPTS or is_expired(challenge.otp_expires_at):
        raise HTTPException(400, "ERR_OTP_INVALID")
    if not hmac.compare_digest(challenge.otp_hash, otp_hash(challenge.challenge_id, data.otp_code)):
        challenge.attempts += 1
        session.add(challenge)
        session.commit()
        raise HTTPException(400, "ERR_OTP_INVALID")
    token = create_token(user.user_id, "password_reset", challenge.challenge_id, timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES))
    challenge.otp_consumed_at = utc_now()
    challenge.reset_hash = credential_hash(token)
    challenge.reset_expires_at = utc_now() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    session.add(challenge)
    session.commit()
    return {"reset_token": token}

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(data: ResetPassword, session: Session = Depends(get_session)):
    payload = decode_token(data.token, "password_reset")
    user = lock_user(session, uuid.UUID(payload["sub"]))
    challenge = session.exec(select(PasswordResetChallenge).where(PasswordResetChallenge.challenge_id == uuid.UUID(payload["sid"])).with_for_update()).first()
    if (not challenge or challenge.user_id != user.user_id or challenge.used_at is not None
            or challenge.otp_consumed_at is None or is_expired(challenge.reset_expires_at)
            or not same_hash(challenge.reset_hash, data.token)):
        raise HTTPException(401, "ERR_TOKEN_INVALID")
    user.hashed_password = get_password_hash(data.new_password)
    session.add(user)
    revoke_user_credentials(session, user)
    result = issue_tokens(session, user)
    session.commit()
    return {**result.model_dump(), "message": "MSG_PASSWORD_RESET_SUCCESS"}

@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserPublic)
def update_user_me(data: UserUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(current_user, key, value)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

@router.put("/security", response_model=UserPublic)
def update_security(data: SecurityUpdate, current_user: User = Depends(get_current_user),
                    auth_session: AuthSession = Depends(get_current_session), session: Session = Depends(get_session)):
    user = lock_user(session, current_user.user_id)
    # Recheck after obtaining the user lock: another password change may have revoked this request's session.
    session.refresh(auth_session)
    if auth_session.revoked_at is not None:
        raise HTTPException(401, "ERR_SESSION_EXPIRED")
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(400, "ERR_OLD_PASSWORD_INCORRECT")
    user.hashed_password = get_password_hash(data.new_password)
    session.add(user)
    revoke_user_credentials(session, user)
    session.commit()
    session.refresh(user)
    return user
