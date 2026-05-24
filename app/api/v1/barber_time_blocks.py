from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.barber_time_block import (
    BarberTimeBlockCreate,
    BarberTimeBlockResponse,
    BarberTimeBlockUpdate,
)
from app.services.barber_time_block_service import (
    create_barber_time_block,
    list_barber_time_blocks,
    set_barber_time_block_active,
    update_barber_time_block,
)


router = APIRouter()


@router.post("/", response_model=BarberTimeBlockResponse)
def create_time_block_api(
    data: BarberTimeBlockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_barber_time_block(db, data, current_user)


@router.get("/", response_model=list[BarberTimeBlockResponse])
def list_time_blocks_api(
    barber_id: int | None = None,
    date_: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_barber_time_blocks(db, current_user, barber_id=barber_id, block_date=date_)


@router.put("/{block_id}", response_model=BarberTimeBlockResponse)
def update_time_block_api(
    block_id: int,
    data: BarberTimeBlockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_barber_time_block(db, block_id, data, current_user)


@router.patch("/{block_id}/activate", response_model=BarberTimeBlockResponse)
def activate_time_block_api(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return set_barber_time_block_active(db, block_id, True, current_user)


@router.delete("/{block_id}", response_model=BarberTimeBlockResponse)
def deactivate_time_block_api(
    block_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return set_barber_time_block_active(db, block_id, False, current_user)
