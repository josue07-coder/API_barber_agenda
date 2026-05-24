from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cash_movement import CashMovement
from app.models.cash_session import CashSession
from app.models.payment import Payment
from app.models.user import User
from app.repositories.cash_register_repo import (
    create_cash_movement,
    create_cash_session,
    get_cash_movement_by_payment_and_type,
    get_cash_movements_by_session,
    get_cash_session_by_id,
    get_open_cash_session_by_branch,
    sum_cash_movements,
    update_cash_session,
)
from app.schema.cash_register import CashMovementCreate, CashSessionClose, CashSessionOpen
from app.services.branch_service import get_active_branch_or_404


def ensure_can_manage_branch_cash(db: Session, current_user: User, branch_id: int) -> None:
    get_active_branch_or_404(db, branch_id)
    if current_user.role == "admin":
        return
    if current_user.role == "barber" and current_user.branch_id == branch_id:
        return
    raise HTTPException(403, "No tienes permiso para gestionar esta caja")


def get_cash_session_or_404(db: Session, session_id: int) -> CashSession:
    session = get_cash_session_by_id(db, session_id)
    if not session:
        raise HTTPException(404, "Caja no encontrada")
    return session


def open_cash_session(db: Session, data: CashSessionOpen, current_user: User) -> CashSession:
    ensure_can_manage_branch_cash(db, current_user, data.branch_id)
    if get_open_cash_session_by_branch(db, data.branch_id):
        raise HTTPException(409, "Ya existe una caja abierta para esta sucursal")

    try:
        return create_cash_session(
            db,
            CashSession(
                branch_id=data.branch_id,
                opened_by_user_id=current_user.id,
                opening_amount=data.opening_amount,
                status="open",
                notes=data.notes,
            ),
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Ya existe una caja abierta para esta sucursal")


def get_current_cash_session(db: Session, branch_id: int, current_user: User) -> CashSession:
    ensure_can_manage_branch_cash(db, current_user, branch_id)
    session = get_open_cash_session_by_branch(db, branch_id)
    if not session:
        raise HTTPException(404, "No hay caja abierta para esta sucursal")
    return session


def get_cash_session(db: Session, session_id: int, current_user: User) -> CashSession:
    session = get_cash_session_or_404(db, session_id)
    ensure_can_manage_branch_cash(db, current_user, session.branch_id)
    return session


def close_cash_session(
    db: Session,
    session_id: int,
    data: CashSessionClose,
    current_user: User,
) -> CashSession:
    session = get_cash_session(db, session_id, current_user)
    if session.status == "closed":
        raise HTTPException(400, "La caja ya esta cerrada")

    income, outgoing = sum_cash_movements(db, session.id)
    expected = Decimal(session.opening_amount) + Decimal(income) - Decimal(outgoing)
    difference = Decimal(data.closing_amount) - expected

    session.status = "closed"
    session.closed_by_user_id = current_user.id
    session.closing_amount = data.closing_amount
    session.expected_amount = expected
    session.difference_amount = difference
    session.closed_at = datetime.now(timezone.utc)
    session.notes = data.notes or session.notes
    return update_cash_session(db, session)


def create_manual_cash_movement(
    db: Session,
    data: CashMovementCreate,
    current_user: User,
) -> CashMovement:
    session = get_cash_session(db, data.cash_session_id, current_user)
    if session.status != "open":
        raise HTTPException(400, "No se permiten movimientos en caja cerrada")

    return create_cash_movement(
        db,
        CashMovement(
            cash_session_id=session.id,
            movement_type=data.movement_type,
            amount=data.amount,
            method=data.method.value,
            description=data.description,
            created_by_user_id=current_user.id,
        ),
    )


def list_cash_movements(db: Session, session_id: int, current_user: User) -> list[CashMovement]:
    session = get_cash_session(db, session_id, current_user)
    return get_cash_movements_by_session(db, session.id)


def create_payment_cash_movement(
    db: Session,
    payment: Payment,
    current_user: User,
    movement_type: str,
) -> CashMovement | None:
    if payment.payment_method != "cash":
        return None

    if get_cash_movement_by_payment_and_type(db, payment.id, movement_type):
        return None

    branch_id = payment.appointment.branch_id
    if branch_id is None:
        return None

    session = get_open_cash_session_by_branch(db, branch_id)
    if not session:
        raise HTTPException(409, "No hay caja abierta para registrar el movimiento cash")

    return create_cash_movement(
        db,
        CashMovement(
            cash_session_id=session.id,
            payment_id=payment.id,
            movement_type=movement_type,
            amount=payment.amount,
            method="cash",
            description=f"Movimiento automatico por pago #{payment.id}",
            created_by_user_id=current_user.id,
        ),
    )
