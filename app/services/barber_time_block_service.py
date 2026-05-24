from datetime import date, time

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.barber_time_block import BarberTimeBlock
from app.models.user import User
from app.repositories.barber_time_block_repo import (
    create_time_block,
    get_active_time_blocks_for_day,
    get_time_block_by_id,
    get_time_blocks,
    update_time_block,
)
from app.schema.barber_time_block import BarberTimeBlockCreate, BarberTimeBlockUpdate
from app.services.barber_schedule_service import (
    ensure_active_barber,
    ensure_can_manage_barber_resource,
    ranges_overlap,
)


def create_barber_time_block(
    db: Session,
    data: BarberTimeBlockCreate,
    current_user: User,
) -> BarberTimeBlock:
    ensure_can_manage_barber_resource(current_user, data.barber_id)
    ensure_active_barber(db, data.barber_id)

    block = BarberTimeBlock(**data.model_dump())

    try:
        return create_time_block(db, block)
    except IntegrityError:
        raise HTTPException(409, "No se pudo crear el bloqueo")


def list_barber_time_blocks(
    db: Session,
    current_user: User,
    barber_id: int | None = None,
    block_date: date | None = None,
) -> list[BarberTimeBlock]:
    if current_user.role == "barber":
        if barber_id is not None and barber_id != current_user.id:
            raise HTTPException(403, "No tienes permiso")
        barber_id = current_user.id
    elif current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")

    return get_time_blocks(db, barber_id=barber_id, block_date=block_date)


def update_barber_time_block(
    db: Session,
    block_id: int,
    data: BarberTimeBlockUpdate,
    current_user: User,
) -> BarberTimeBlock:
    block = get_time_block_by_id(db, block_id)
    if not block:
        raise HTTPException(404, "Bloqueo no encontrado")

    ensure_can_manage_barber_resource(current_user, block.barber_id)

    values = data.model_dump(exclude_unset=True)
    is_full_day = values.get("is_full_day", block.is_full_day)
    start_time = values.get("start_time", block.start_time)
    end_time = values.get("end_time", block.end_time)

    if is_full_day:
        start_time = None
        end_time = None
        values["start_time"] = None
        values["end_time"] = None
    else:
        if start_time is None or end_time is None:
            raise HTTPException(400, "Un bloqueo parcial requiere start_time y end_time")
        if start_time >= end_time:
            raise HTTPException(400, "start_time debe ser menor que end_time")

    for field, value in values.items():
        setattr(block, field, value)

    try:
        return update_time_block(db, block)
    except IntegrityError:
        raise HTTPException(409, "No se pudo actualizar el bloqueo")


def set_barber_time_block_active(
    db: Session,
    block_id: int,
    is_active: bool,
    current_user: User,
) -> BarberTimeBlock:
    block = get_time_block_by_id(db, block_id)
    if not block:
        raise HTTPException(404, "Bloqueo no encontrado")

    ensure_can_manage_barber_resource(current_user, block.barber_id)
    block.is_active = is_active
    return update_time_block(db, block)


def appointment_is_blocked(
    db: Session,
    *,
    barber_id: int,
    appointment_date: date,
    start_time: time,
    end_time: time,
) -> bool:
    blocks = get_active_time_blocks_for_day(db, barber_id, appointment_date)

    for block in blocks:
        if block.is_full_day:
            return True
        if ranges_overlap(start_time, end_time, block.start_time, block.end_time):
            return True

    return False


def get_active_blocks_for_day(
    db: Session,
    *,
    barber_id: int,
    block_date: date,
) -> list[BarberTimeBlock]:
    return get_active_time_blocks_for_day(db, barber_id, block_date)
