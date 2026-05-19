import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from backend.app.core.db import get_session
from backend.app.models.models import Notification, User
from backend.app.schemas.schemas import NotificationResponse
from backend.app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách tất cả thông báo của người dùng hiện tại (sắp xếp mới nhất lên đầu).
    """
    notifications = session.exec(
        select(Notification)
        .where(Notification.user_id == current_user.user_id)
        .order_by(Notification.created_at.desc())
    ).all()
    return notifications

@router.post("/read", status_code=status.HTTP_200_OK)
def mark_all_as_read(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Đánh dấu tất cả thông báo của người dùng hiện tại là đã đọc.
    """
    notifications = session.exec(
        select(Notification)
        .where(Notification.user_id == current_user.user_id, Notification.is_read == False)
    ).all()

    for notification in notifications:
        notification.is_read = True
        session.add(notification)
    
    session.commit()
    return {"message": "MSG_MARK_ALL_READ_SUCCESS"}

@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_single_as_read(
    notification_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Đánh dấu một thông báo cụ thể là đã đọc.
    """
    notification = session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ERR_NOTIFICATION_NOT_FOUND"
        )
    
    notification.is_read = True
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification
