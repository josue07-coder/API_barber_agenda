from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.barber_schedule import (
    BarberScheduleCreate,
    BarberScheduleResponse,
    BarberScheduleUpdate,
)
from app.services.barber_schedule_service import (
    create_barber_schedule,
    list_barber_schedules,
    set_barber_schedule_active,
    update_barber_schedule,
)


router = APIRouter()


@router.post("/", response_model=BarberScheduleResponse)
def create_schedule_api(
    data: BarberScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_barber_schedule(db, data, current_user)


@router.get("/barber/{barber_id}", response_model=list[BarberScheduleResponse])
def list_schedules_api(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_barber_schedules(db, barber_id, current_user)


@router.put("/{schedule_id}", response_model=BarberScheduleResponse)
def update_schedule_api(
    schedule_id: int,
    data: BarberScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_barber_schedule(db, schedule_id, data, current_user)


@router.patch("/{schedule_id}/activate", response_model=BarberScheduleResponse)
def activate_schedule_api(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return set_barber_schedule_active(db, schedule_id, True, current_user)


@router.patch("/{schedule_id}/deactivate", response_model=BarberScheduleResponse)
def deactivate_schedule_api(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return set_barber_schedule_active(db, schedule_id, False, current_user)
