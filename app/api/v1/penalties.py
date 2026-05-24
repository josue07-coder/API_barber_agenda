from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.client_penalty import ClientPenaltyResponse, PenaltyResolution
from app.services.client_penalty_service import (
    cancel_penalty,
    forgive_penalty,
    mark_penalty_paid,
)


router = APIRouter()


@router.patch(
    "/{penalty_id}/forgive",
    response_model=ClientPenaltyResponse,
    summary="Perdonar penalizacion",
    description="Marca una penalizacion como perdonada. Requiere admin.",
)
def forgive_penalty_api(
    penalty_id: int,
    data: PenaltyResolution | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return forgive_penalty(db, penalty_id, data or PenaltyResolution(), current_user)


@router.patch(
    "/{penalty_id}/mark-paid",
    response_model=ClientPenaltyResponse,
    summary="Marcar penalizacion como pagada",
    description="Marca una penalizacion como pagada. Requiere admin.",
)
def mark_penalty_paid_api(
    penalty_id: int,
    data: PenaltyResolution | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return mark_penalty_paid(db, penalty_id, data or PenaltyResolution(), current_user)


@router.patch(
    "/{penalty_id}/cancel",
    response_model=ClientPenaltyResponse,
    summary="Cancelar penalizacion",
    description="Cancela una penalizacion sin eliminar el registro. Requiere admin.",
)
def cancel_penalty_api(
    penalty_id: int,
    data: PenaltyResolution | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return cancel_penalty(db, penalty_id, data or PenaltyResolution(), current_user)
