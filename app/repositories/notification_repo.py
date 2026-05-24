from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.notification import Notification


def create_notification(db: Session, notification: Notification) -> Notification:
    try:
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
    except IntegrityError:
        db.rollback()
        raise


def get_notification_by_id(db: Session, notification_id: int) -> Notification | None:
    return db.query(Notification).filter(Notification.id == notification_id).first()


def get_notifications(db: Session, skip: int = 0, limit: int = 50) -> list[Notification]:
    return (
        db.query(Notification)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_notifications_for_barber(
    db: Session,
    barber_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[Notification]:
    return (
        db.query(Notification)
        .outerjoin(
            Appointment,
            (Notification.related_type == "appointment")
            & (Notification.related_id == Appointment.id),
        )
        .filter(
            (
                (Notification.recipient_type == "barber")
                & (Notification.recipient_id == barber_id)
            )
            | (Appointment.user_id == barber_id)
        )
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_notifications_for_client(
    db: Session,
    client_id: int,
    skip: int = 0,
    limit: int = 50,
) -> list[Notification]:
    return (
        db.query(Notification)
        .filter(
            Notification.recipient_type == "client",
            Notification.recipient_id == client_id,
        )
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_notification(db: Session, notification: Notification) -> Notification:
    try:
        db.commit()
        db.refresh(notification)
        return notification
    except IntegrityError:
        db.rollback()
        raise


def reminder_exists(
    db: Session,
    *,
    recipient_type: str,
    recipient_id: int,
    appointment_id: int,
    reminder_key: str,
    scheduled_for: datetime,
) -> bool:
    return (
        db.query(Notification.id)
        .filter(
            Notification.recipient_type == recipient_type,
            Notification.recipient_id == recipient_id,
            Notification.related_type == "appointment",
            Notification.related_id == appointment_id,
            Notification.subject == f"appointment_reminder_{reminder_key}",
            Notification.scheduled_for == scheduled_for,
        )
        .first()
        is not None
    )


def get_appointments_for_reminders(db: Session, now: datetime) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(
            Appointment.status.in_(["agendada", "confirmada"]),
            Appointment.date >= now.date(),
        )
        .all()
    )
