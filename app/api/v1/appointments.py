from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database.session import get_db
from app.schema.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AvailableSlotsResponse,
    AppointmentStatusUpdate,
    AppointmentCancel,
    AppointmentHistoryResponse,
    AppointmentReschedule,
)
from app.services.appointment_service import (
    create_new_appointment,
    update_existing_appointment,
    cancel_appointment,
    change_appointment_status,
    list_all_appointments,
    list_appointments_by_barber,
    list_appointments_by_client,
    list_appointments_by_day,
    list_appointment_history,
    get_available_slots,
    reschedule_appointment,
    update_appointment_status
)
from app.models.appointment_status import AppointmentStatus
from app.api.deps import get_current_user, require_role
from app.models.user import User

router = APIRouter()


#crear cita
@router.post("/", response_model=AppointmentResponse)
def create_appointment_api(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "barber" and data.barber_id != current_user.id:
        raise HTTPException(403)
    return create_new_appointment(db, data, current_user)

@router.get("/", response_model=List[AppointmentResponse])
def get_all_appointments_api(
    barber_id: int | None = None,
    branch_id: int | None = None,
    client_id: int | None = None,
    date_: date | None = None,
    status: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    return list_all_appointments(
        db,
        current_user=current_user,
        barber_id=barber_id,
        branch_id=branch_id,
        client_id=client_id,
        appointment_date=date_,
        status=status,
        skip=skip,
        limit=limit
    )


# listar citas por dias
@router.get(
    "/day",
    response_model=List[AppointmentResponse]
)
def get_appointments_by_day_api(
    barber_id: int,
    date_: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "barber" and barber_id != current_user.id:
        raise HTTPException(403, "No autorizado")
    
    return list_appointments_by_day(
        db,
        barber_id=barber_id,
        appointment_date=date_
    )

# listar citas por barbero
@router.get(
    "/barber/{barber_id}",
    response_model=List[AppointmentResponse]
)
def get_appointments_by_barber_api(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "barber" and barber_id != current_user.id:
        raise HTTPException(403, "No autorizado")
    return list_appointments_by_barber(db, barber_id)

# listar citas por clientes
@router.get(
    "/client/{client_id}",
    response_model=List[AppointmentResponse]
)
def get_appointments_by_client_api(
    client_id: int,
    db: Session = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    return list_appointments_by_client(db, client_id)

# actualizar citas
@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse
)
def update_appointment_api(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return update_existing_appointment(
        db,
        appointment_id,
        data.dict(exclude_unset=True),
        current_user
    )

# cancelar citas
@router.delete("/{appointment_id}", status_code=204)
def cancel_appointment_api(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cancel_appointment(db, appointment_id, current_user)


@router.patch("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment_patch_api(
    appointment_id: int,
    data: AppointmentCancel | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cancel_appointment(
        db,
        appointment_id,
        current_user,
        reason=data.reason if data else None,
    )


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment_api(
    appointment_id: int,
    data: AppointmentReschedule,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return reschedule_appointment(db, appointment_id, data, current_user)


@router.patch("/{appointment_id}/confirm", response_model=AppointmentResponse)
def confirm_appointment_api(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return change_appointment_status(
        db,
        appointment_id,
        AppointmentStatus.confirmada,
        current_user,
    )


@router.patch("/{appointment_id}/complete", response_model=AppointmentResponse)
def complete_appointment_api(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return change_appointment_status(
        db,
        appointment_id,
        AppointmentStatus.completada,
        current_user,
    )


@router.patch("/{appointment_id}/no-show", response_model=AppointmentResponse)
def no_show_appointment_api(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return change_appointment_status(
        db,
        appointment_id,
        AppointmentStatus.no_show,
        current_user,
    )


@router.get("/{appointment_id}/history", response_model=List[AppointmentHistoryResponse])
def get_appointment_history_api(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_appointment_history(db, appointment_id, current_user)

# obtener horarios disponibles
@router.get(
    "/available-slots",
    response_model=AvailableSlotsResponse
)
def get_available_slots_api(
    barber_id: int,
    service_id: int,
    date_: date = Query(..., alias="date"),
    branch_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
   current_user: User = Depends(get_current_user)
):
    if current_user.role == "barber" and barber_id != current_user.id:
        raise HTTPException(403, "No autorizado")
     
    slots = get_available_slots(
        db,
        barber_id=barber_id,
        service_id=service_id,
        appointment_date=date_,
        branch_id=branch_id,
    )
    return {"slots": slots}

@router.patch("/{appointment_id}/status")
def change_status(
    appointment_id: int,
    data: AppointmentStatusUpdate = Body(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        return update_appointment_status(
            db,
            appointment_id,
            data.status,
            current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))




