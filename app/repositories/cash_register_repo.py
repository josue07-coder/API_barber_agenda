from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cash_movement import CashMovement
from app.models.cash_session import CashSession


def create_cash_session(db: Session, session: CashSession) -> CashSession:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_cash_session_by_id(db: Session, session_id: int) -> CashSession | None:
    return db.query(CashSession).filter(CashSession.id == session_id).first()


def get_open_cash_session_by_branch(db: Session, branch_id: int) -> CashSession | None:
    return (
        db.query(CashSession)
        .filter(CashSession.branch_id == branch_id, CashSession.status == "open")
        .first()
    )


def update_cash_session(db: Session, session: CashSession) -> CashSession:
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_cash_movement(db: Session, movement: CashMovement) -> CashMovement:
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def get_cash_movements_by_session(db: Session, session_id: int) -> list[CashMovement]:
    return (
        db.query(CashMovement)
        .filter(CashMovement.cash_session_id == session_id)
        .order_by(CashMovement.created_at, CashMovement.id)
        .all()
    )


def get_cash_movement_by_payment_and_type(
    db: Session,
    payment_id: int,
    movement_type: str,
) -> CashMovement | None:
    return (
        db.query(CashMovement)
        .filter(CashMovement.payment_id == payment_id, CashMovement.movement_type == movement_type)
        .first()
    )


def sum_cash_movements(db: Session, session_id: int):
    income = (
        db.query(func.coalesce(func.sum(CashMovement.amount), 0))
        .filter(
            CashMovement.cash_session_id == session_id,
            CashMovement.movement_type.in_(["income", "adjustment"]),
        )
        .scalar()
    )
    outgoing = (
        db.query(func.coalesce(func.sum(CashMovement.amount), 0))
        .filter(
            CashMovement.cash_session_id == session_id,
            CashMovement.movement_type.in_(["expense", "refund"]),
        )
        .scalar()
    )
    return income or 0, outgoing or 0
