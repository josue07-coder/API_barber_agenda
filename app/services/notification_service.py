from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.notification import Notification
from app.models.notification_channel import NotificationChannel
from app.models.notification_status import NotificationStatus
from app.models.payment import Payment
from app.models.user import User
from app.repositories.appointment_repo import get_appointment_by_id
from app.repositories.notification_repo import (
    create_notification,
    get_appointments_for_reminders,
    get_notification_by_id,
    get_notifications,
    get_notifications_for_barber,
    get_notifications_for_client,
    reminder_exists,
    update_notification,
)
from app.repositories.payment_repo import get_payment_by_id
from app.schema.notification import NotificationFailed
from app.services.branch_service import get_effective_branch_settings


EVENT_SUBJECTS = {
    "appointment_created": "Cita creada",
    "appointment_confirmed": "Cita confirmada",
    "appointment_rescheduled": "Cita reprogramada",
    "appointment_cancelled": "Cita cancelada",
    "appointment_completed": "Cita completada",
    "payment_registered": "Pago registrado",
    "payment_refunded": "Pago reembolsado",
}


def appointment_datetime(appointment: Appointment) -> datetime:
    return datetime.combine(appointment.date, appointment.start_time).replace(tzinfo=timezone.utc)


def create_internal_notification(
    db: Session,
    *,
    recipient_type: str,
    recipient_id: int,
    subject: str,
    message: str,
    related_type: str | None = None,
    related_id: int | None = None,
    scheduled_for: datetime | None = None,
    channel: NotificationChannel = NotificationChannel.in_app,
) -> Notification:
    return create_notification(
        db,
        Notification(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            channel=channel.value,
            subject=subject,
            message=message,
            status=NotificationStatus.pending.value,
            related_type=related_type,
            related_id=related_id,
            scheduled_for=scheduled_for,
        ),
    )


def notify_appointment_event(db: Session, appointment: Appointment, event: str) -> Notification:
    subject = EVENT_SUBJECTS[event]
    message = (
        f"{subject}: cita #{appointment.id} para el {appointment.date.isoformat()} "
        f"a las {appointment.start_time.isoformat()}."
    )
    barber_notification = create_internal_notification(
        db,
        recipient_type="barber",
        recipient_id=appointment.user_id,
        subject=event,
        message=message,
        related_type="appointment",
        related_id=appointment.id,
    )
    create_internal_notification(
        db,
        recipient_type="client",
        recipient_id=appointment.client_id,
        subject=event,
        message=message,
        related_type="appointment",
        related_id=appointment.id,
    )
    return barber_notification


def notify_payment_event(db: Session, payment: Payment, event: str) -> Notification:
    appointment = payment.appointment
    subject = EVENT_SUBJECTS[event]
    message = f"{subject}: pago #{payment.id} por {payment.amount} {payment.currency}."
    barber_notification = create_internal_notification(
        db,
        recipient_type="barber",
        recipient_id=appointment.user_id,
        subject=event,
        message=message,
        related_type="payment",
        related_id=payment.id,
    )
    create_internal_notification(
        db,
        recipient_type="client",
        recipient_id=appointment.client_id,
        subject=event,
        message=message,
        related_type="payment",
        related_id=payment.id,
    )
    return barber_notification


def notification_related_appointment(db: Session, notification: Notification) -> Appointment | None:
    if notification.related_type == "appointment" and notification.related_id:
        return get_appointment_by_id(db, notification.related_id)

    if notification.related_type == "payment" and notification.related_id:
        payment = get_payment_by_id(db, notification.related_id)
        return payment.appointment if payment else None

    return None


def ensure_can_access_notification(
    db: Session,
    current_user: User,
    notification: Notification,
) -> None:
    if current_user.role == "admin":
        return

    if current_user.role == "barber":
        related_appointment = notification_related_appointment(db, notification)
        if (
            notification.recipient_type == "barber"
            and notification.recipient_id == current_user.id
        ):
            return
        if related_appointment and related_appointment.user_id == current_user.id:
            return

    if (
        current_user.role == "client"
        and notification.recipient_type == "client"
        and notification.recipient_id == current_user.client_id
    ):
        return

    raise HTTPException(403, "No tienes permiso para acceder a esta notificacion")


def list_notifications(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 50,
) -> list[Notification]:
    if current_user.role == "admin":
        return get_notifications(db, skip, limit)

    if current_user.role == "barber":
        return get_notifications_for_barber(db, current_user.id, skip, limit)

    if current_user.role == "client" and current_user.client_id is not None:
        return get_notifications_for_client(db, current_user.client_id, skip, limit)

    raise HTTPException(403, "No tienes permiso")


def get_notification(db: Session, notification_id: int, current_user: User) -> Notification:
    notification = get_notification_by_id(db, notification_id)
    if not notification:
        raise HTTPException(404, "Notificacion no encontrada")

    ensure_can_access_notification(db, current_user, notification)
    return notification


def mark_notification_sent(
    db: Session,
    notification_id: int,
    current_user: User,
) -> Notification:
    notification = get_notification(db, notification_id, current_user)
    notification.status = NotificationStatus.sent.value
    notification.sent_at = datetime.now(timezone.utc)
    notification.failed_at = None
    notification.error_message = None
    return update_notification(db, notification)


def mark_notification_failed(
    db: Session,
    notification_id: int,
    data: NotificationFailed,
    current_user: User,
) -> Notification:
    notification = get_notification(db, notification_id, current_user)
    notification.status = NotificationStatus.failed.value
    notification.failed_at = datetime.now(timezone.utc)
    notification.error_message = data.error_message
    return update_notification(db, notification)


def cancel_notification(
    db: Session,
    notification_id: int,
    current_user: User,
) -> Notification:
    notification = get_notification(db, notification_id, current_user)
    notification.status = NotificationStatus.cancelled.value
    return update_notification(db, notification)


def generate_due_reminders(
    db: Session,
    current_user: User,
    now: datetime | None = None,
) -> int:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    created = 0
    for appointment in get_appointments_for_reminders(db, now):
        appt_dt = appointment_datetime(appointment)
        if appt_dt <= now:
            continue

        for reminder_key, delta in (("24h", timedelta(hours=24)), ("2h", timedelta(hours=2))):
            branch_settings = get_effective_branch_settings(db, appointment.branch_id)
            if reminder_key == "24h" and branch_settings and not branch_settings.reminder_24h_enabled:
                continue
            if reminder_key == "2h" and branch_settings and not branch_settings.reminder_2h_enabled:
                continue

            scheduled_for = appt_dt - delta
            if scheduled_for > now:
                continue

            for recipient_type, recipient_id in (
                ("barber", appointment.user_id),
                ("client", appointment.client_id),
            ):
                if reminder_exists(
                    db,
                    recipient_type=recipient_type,
                    recipient_id=recipient_id,
                    appointment_id=appointment.id,
                    reminder_key=reminder_key,
                    scheduled_for=scheduled_for,
                ):
                    continue

                create_internal_notification(
                    db,
                    recipient_type=recipient_type,
                    recipient_id=recipient_id,
                    subject=f"appointment_reminder_{reminder_key}",
                    message=(
                        f"Recordatorio {reminder_key}: cita #{appointment.id} "
                        f"programada para {appointment.date.isoformat()} "
                        f"a las {appointment.start_time.isoformat()}."
                    ),
                    related_type="appointment",
                    related_id=appointment.id,
                    scheduled_for=scheduled_for,
                )
                created += 1

    return created
