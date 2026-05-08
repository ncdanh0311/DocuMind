from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import timedelta
from backend.app.core.db import get_session
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.config import settings
from backend.app.models.models import User
from backend.app.schemas.schemas import UserCreate, UserLogin, Token, UserPublic

router = APIRouter()

@router.post("/register", response_model=Token)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    # Kiểm tra email đã tồn tại chưa
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email này đã được sử dụng."
        )
    
    # Tạo user mới
    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password)
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    # Tạo token để đăng nhập ngay lặp tức
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
    # Tìm user theo email
    user = session.exec(select(User).where(User.email == user_in.email)).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Tạo JWT Token
    access_token = create_access_token(subject=user.user_id)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "full_name": user.full_name
    }
