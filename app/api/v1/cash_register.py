from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.cash_register import (
    CashMovementCreate,
    CashMovementResponse,
    CashSessionClose,
    CashSessionOpen,
    CashSessionResponse,
)
from app.services.cash_register_service import (
    close_cash_session,
    create_manual_cash_movement,
    get_cash_session,
    get_current_cash_session,
    list_cash_movements,
    open_cash_session,
)


router = APIRouter()


@router.post("/cash-sessions/open", response_model=CashSessionResponse, tags=["Cash register"])
def open_cash_session_api(
    data: CashSessionOpen,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return open_cash_session(db, data, current_user)


@router.patch("/cash-sessions/{session_id}/close", response_model=CashSessionResponse, tags=["Cash register"])
def close_cash_session_api(
    session_id: int,
    data: CashSessionClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return close_cash_session(db, session_id, data, current_user)


@router.get("/cash-sessions/current", response_model=CashSessionResponse, tags=["Cash register"])
def current_cash_session_api(
    branch_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_current_cash_session(db, branch_id, current_user)


@router.get("/cash-sessions/{session_id}", response_model=CashSessionResponse, tags=["Cash register"])
def get_cash_session_api(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_cash_session(db, session_id, current_user)


@router.post("/cash-movements/", response_model=CashMovementResponse, tags=["Cash register"])
def create_cash_movement_api(
    data: CashMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_manual_cash_movement(db, data, current_user)


@router.get("/cash-movements/session/{session_id}", response_model=list[CashMovementResponse], tags=["Cash register"])
def list_cash_movements_api(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_cash_movements(db, session_id, current_user)
