from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.barber_time_block import BarberTimeBlock


def create_time_block(db: Session, block: BarberTimeBlock) -> BarberTimeBlock:
    try:
        db.add(block)
        db.commit()
        db.refresh(block)
        return block
    except IntegrityError:
        db.rollback()
        raise


def get_time_block_by_id(db: Session, block_id: int) -> BarberTimeBlock | None:
    return db.query(BarberTimeBlock).filter(BarberTimeBlock.id == block_id).first()


def get_time_blocks(
    db: Session,
    barber_id: int | None = None,
    block_date: date | None = None,
) -> list[BarberTimeBlock]:
    query = db.query(BarberTimeBlock)

    if barber_id is not None:
        query = query.filter(BarberTimeBlock.barber_id == barber_id)

    if block_date is not None:
        query = query.filter(BarberTimeBlock.date == block_date)

    return query.order_by(BarberTimeBlock.date, BarberTimeBlock.start_time).all()


def get_active_time_blocks_for_day(
    db: Session,
    barber_id: int,
    block_date: date,
) -> list[BarberTimeBlock]:
    return (
        db.query(BarberTimeBlock)
        .filter(
            BarberTimeBlock.barber_id == barber_id,
            BarberTimeBlock.date == block_date,
            BarberTimeBlock.is_active == True,
        )
        .order_by(BarberTimeBlock.start_time)
        .all()
    )


def update_time_block(db: Session, block: BarberTimeBlock) -> BarberTimeBlock:
    try:
        db.commit()
        db.refresh(block)
        return block
    except IntegrityError:
        db.rollback()
        raise
