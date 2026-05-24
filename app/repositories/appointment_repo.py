from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.models.appointment import Appointment


def create_appointment(db: Session, appointment: Appointment) -> Appointment:
    try:
        db.add(appointment)
        db.commit()
        db.refresh(appointment)
        return appointment
    except IntegrityError:
        db.rollback()
        raise


def get_appointments(
    db: Session,
    *,
    barber_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    client_id: Optional[int] = None,
    appointment_date: Optional[date] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    query = db.query(Appointment)

    if barber_id is not None:
        query = query.filter(Appointment.user_id == barber_id)

    if branch_id is not None:
        query = query.filter(Appointment.branch_id == branch_id)

    if client_id is not None:
        query = query.filter(Appointment.client_id == client_id)

    if appointment_date is not None:
        query = query.filter(Appointment.date == appointment_date)

    if status is not None:
        query = query.filter(Appointment.status == status)

    query = query.order_by(Appointment.date, Appointment.start_time)

    return query.offset(skip).limit(limit).all()


def get_appointment_by_id(
    db: Session,
    appointment_id: int
) -> Appointment | None:
    return (
        db.query(Appointment)
        .filter(Appointment.id == appointment_id)
        .first()
    )


def get_appointments_by_day(
    db: Session,
    barber_id: int,
    day: date
) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(
            Appointment.user_id == barber_id,
            Appointment.date == day,
            Appointment.status.notin_(["cancelada", "no_show"])
        )
        .order_by(Appointment.start_time)
        .all()
    )


def get_appointments_by_day_for_update(
    db: Session,
    barber_id: int,
    day: date
) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(
            Appointment.user_id == barber_id,
            Appointment.date == day,
            Appointment.status.notin_(["cancelada", "no_show"])
        )
        .order_by(Appointment.start_time)
        .with_for_update()
        .all()
    )


def get_appointments_by_barber(
    db: Session,
    barber_id: int
) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(Appointment.user_id == barber_id)
        .order_by(Appointment.date, Appointment.start_time)
        .all()
    )


def get_appointments_by_client(
    db: Session,
    client_id: int
) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(Appointment.client_id == client_id)
        .order_by(Appointment.date, Appointment.start_time)
        .all()
    )


def update_appointment(
    db: Session,
    appointment: Appointment
) -> Appointment:
    try:
        db.commit()
        db.refresh(appointment)
        return appointment
    except IntegrityError:
        db.rollback()
        raise


def flush_appointment(
    db: Session,
    appointment: Appointment
) -> Appointment:
    try:
        db.flush()
        return appointment
    except IntegrityError:
        db.rollback()
        raise
