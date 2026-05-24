from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.barber_schedule import BarberSchedule


def create_schedule(db: Session, schedule: BarberSchedule) -> BarberSchedule:
    try:
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        return schedule
    except IntegrityError:
        db.rollback()
        raise


def get_schedule_by_id(db: Session, schedule_id: int) -> BarberSchedule | None:
    return db.query(BarberSchedule).filter(BarberSchedule.id == schedule_id).first()


def get_schedules_by_barber(db: Session, barber_id: int) -> list[BarberSchedule]:
    return (
        db.query(BarberSchedule)
        .filter(BarberSchedule.barber_id == barber_id)
        .order_by(BarberSchedule.weekday, BarberSchedule.start_time)
        .all()
    )


def get_active_schedules_for_day(
    db: Session,
    barber_id: int,
    weekday: int,
) -> list[BarberSchedule]:
    return (
        db.query(BarberSchedule)
        .filter(
            BarberSchedule.barber_id == barber_id,
            BarberSchedule.weekday == weekday,
            BarberSchedule.is_active == True,
        )
        .order_by(BarberSchedule.start_time)
        .all()
    )


def update_schedule(db: Session, schedule: BarberSchedule) -> BarberSchedule:
    try:
        db.commit()
        db.refresh(schedule)
        return schedule
    except IntegrityError:
        db.rollback()
        raise
