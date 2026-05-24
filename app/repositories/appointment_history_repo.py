from sqlalchemy.orm import Session

from app.models.appointment_history import AppointmentHistory


def create_appointment_history(
    db: Session,
    history: AppointmentHistory,
) -> AppointmentHistory:
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_history_by_appointment(
    db: Session,
    appointment_id: int,
) -> list[AppointmentHistory]:
    return (
        db.query(AppointmentHistory)
        .filter(AppointmentHistory.appointment_id == appointment_id)
        .order_by(AppointmentHistory.created_at, AppointmentHistory.id)
        .all()
    )
