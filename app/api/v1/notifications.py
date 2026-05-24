from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.notification import (
    GenerateRemindersResponse,
    NotificationFailed,
    NotificationResponse,
)
from app.services.notification_service import (
    cancel_notification,
    generate_due_reminders,
    get_notification,
    list_notifications,
    mark_notification_failed,
    mark_notification_sent,
)


router = APIRouter()


@router.get("/", response_model=list[NotificationResponse])
def list_notifications_api(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_notifications(db, current_user, skip, limit)


@router.post("/generate-reminders", response_model=GenerateRemindersResponse)
def generate_reminders_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"created": generate_due_reminders(db, current_user)}


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification_api(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_notification(db, notification_id, current_user)


@router.patch("/{notification_id}/mark-sent", response_model=NotificationResponse)
def mark_sent_api(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return mark_notification_sent(db, notification_id, current_user)


@router.patch("/{notification_id}/mark-failed", response_model=NotificationResponse)
def mark_failed_api(
    notification_id: int,
    data: NotificationFailed,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return mark_notification_failed(db, notification_id, data, current_user)


@router.patch("/{notification_id}/cancel", response_model=NotificationResponse)
def cancel_notification_api(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cancel_notification(db, notification_id, current_user)
