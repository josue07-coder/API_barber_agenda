from datetime import date, time

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.barber_schedule import BarberSchedule
from app.models.user import User
from app.repositories.barber_schedule_repo import (
    create_schedule,
    get_active_schedules_for_day,
    get_schedule_by_id,
    get_schedules_by_barber,
    update_schedule,
)
from app.repositories.user_repo import get_user_by_id
from app.schema.barber_schedule import BarberScheduleCreate, BarberScheduleUpdate


def ensure_can_manage_barber_resource(current_user: User, barber_id: int) -> None:
    if current_user.role == "admin":
        return

    if current_user.role == "barber" and current_user.id == barber_id:
        return

    raise HTTPException(403, "No tienes permiso")


def ensure_active_barber(db: Session, barber_id: int) -> User:
    barber = get_user_by_id(db, barber_id)
    if not barber or not barber.is_active:
        raise HTTPException(404, "Barbero no encontrado")
    if barber.role != "barber":
        raise HTTPException(400, "El usuario seleccionado no es un barbero")
    return barber


def ranges_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return start_a < end_b and end_a > start_b


def validate_schedule_overlap(
    db: Session,
    *,
    barber_id: int,
    weekday: int,
    start_time: time,
    end_time: time,
    exclude_schedule_id: int | None = None,
) -> None:
    schedules = get_active_schedules_for_day(db, barber_id, weekday)
    for schedule in schedules:
        if exclude_schedule_id is not None and schedule.id == exclude_schedule_id:
            continue
        if ranges_overlap(start_time, end_time, schedule.start_time, schedule.end_time):
            raise HTTPException(409, "El horario se solapa con otro horario activo")


def create_barber_schedule(
    db: Session,
    data: BarberScheduleCreate,
    current_user: User,
) -> BarberSchedule:
    ensure_can_manage_barber_resource(current_user, data.barber_id)
    ensure_active_barber(db, data.barber_id)
    validate_schedule_overlap(
        db,
        barber_id=data.barber_id,
        weekday=data.weekday,
        start_time=data.start_time,
        end_time=data.end_time,
    )

    schedule = BarberSchedule(**data.model_dump())

    try:
        return create_schedule(db, schedule)
    except IntegrityError:
        raise HTTPException(409, "No se pudo crear el horario")


def list_barber_schedules(
    db: Session,
    barber_id: int,
    current_user: User,
) -> list[BarberSchedule]:
    ensure_can_manage_barber_resource(current_user, barber_id)
    ensure_active_barber(db, barber_id)
    return get_schedules_by_barber(db, barber_id)


def update_barber_schedule(
    db: Session,
    schedule_id: int,
    data: BarberScheduleUpdate,
    current_user: User,
) -> BarberSchedule:
    schedule = get_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(404, "Horario no encontrado")

    ensure_can_manage_barber_resource(current_user, schedule.barber_id)

    values = data.model_dump(exclude_unset=True)
    new_weekday = values.get("weekday", schedule.weekday)
    new_start = values.get("start_time", schedule.start_time)
    new_end = values.get("end_time", schedule.end_time)
    new_break_start = values.get("break_start_time", schedule.break_start_time)
    new_break_end = values.get("break_end_time", schedule.break_end_time)

    if new_start >= new_end:
        raise HTTPException(400, "start_time debe ser menor que end_time")

    if (new_break_start is None) != (new_break_end is None):
        raise HTTPException(400, "break_start_time y break_end_time deben enviarse juntos")

    if new_break_start is not None and new_break_end is not None:
        if new_break_start >= new_break_end:
            raise HTTPException(400, "break_start_time debe ser menor que break_end_time")
        if new_break_start < new_start or new_break_end > new_end:
            raise HTTPException(400, "El descanso debe estar dentro del horario")

    if values.get("is_active", schedule.is_active):
        validate_schedule_overlap(
            db,
            barber_id=schedule.barber_id,
            weekday=new_weekday,
            start_time=new_start,
            end_time=new_end,
            exclude_schedule_id=schedule.id,
        )

    for field, value in values.items():
        setattr(schedule, field, value)

    try:
        return update_schedule(db, schedule)
    except IntegrityError:
        raise HTTPException(409, "No se pudo actualizar el horario")


def set_barber_schedule_active(
    db: Session,
    schedule_id: int,
    is_active: bool,
    current_user: User,
) -> BarberSchedule:
    schedule = get_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(404, "Horario no encontrado")

    ensure_can_manage_barber_resource(current_user, schedule.barber_id)

    if is_active:
        validate_schedule_overlap(
            db,
            barber_id=schedule.barber_id,
            weekday=schedule.weekday,
            start_time=schedule.start_time,
            end_time=schedule.end_time,
            exclude_schedule_id=schedule.id,
        )

    schedule.is_active = is_active
    return update_schedule(db, schedule)


def get_schedule_covering_time(
    db: Session,
    *,
    barber_id: int,
    appointment_date: date,
    start_time: time,
    end_time: time,
) -> BarberSchedule | None:
    weekday = appointment_date.weekday()
    schedules = get_active_schedules_for_day(db, barber_id, weekday)

    for schedule in schedules:
        if start_time >= schedule.start_time and end_time <= schedule.end_time:
            return schedule

    return None
