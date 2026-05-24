from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.client_penalty import ClientPenalty


def create_penalty(db: Session, penalty: ClientPenalty) -> ClientPenalty:
    db.add(penalty)
    db.commit()
    db.refresh(penalty)
    return penalty


def update_penalty(db: Session, penalty: ClientPenalty) -> ClientPenalty:
    db.add(penalty)
    db.commit()
    db.refresh(penalty)
    return penalty


def get_penalty_by_id(db: Session, penalty_id: int) -> ClientPenalty | None:
    return db.query(ClientPenalty).filter(ClientPenalty.id == penalty_id).first()


def get_penalties_by_client(db: Session, client_id: int) -> list[ClientPenalty]:
    return (
        db.query(ClientPenalty)
        .filter(ClientPenalty.client_id == client_id)
        .order_by(ClientPenalty.created_at.desc(), ClientPenalty.id.desc())
        .all()
    )


def get_penalty_by_appointment_and_type(
    db: Session,
    appointment_id: int,
    penalty_type: str,
) -> ClientPenalty | None:
    return (
        db.query(ClientPenalty)
        .filter(
            ClientPenalty.appointment_id == appointment_id,
            ClientPenalty.penalty_type == penalty_type,
        )
        .first()
    )


def get_active_penalty_points(db: Session, client_id: int) -> int:
    return (
        db.query(func.coalesce(func.sum(ClientPenalty.points), 0))
        .filter(
            ClientPenalty.client_id == client_id,
            ClientPenalty.status == "active",
        )
        .scalar()
        or 0
    )


def get_penalties_for_barber(db: Session, barber_id: int) -> list[ClientPenalty]:
    return (
        db.query(ClientPenalty)
        .join(Appointment, ClientPenalty.appointment_id == Appointment.id)
        .filter(Appointment.user_id == barber_id)
        .order_by(ClientPenalty.created_at.desc(), ClientPenalty.id.desc())
        .all()
    )


def penalty_report(
    db: Session,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> dict:
    base = db.query(ClientPenalty)
    if start_at is not None:
        base = base.filter(ClientPenalty.created_at >= start_at)
    if end_at is not None:
        base = base.filter(ClientPenalty.created_at <= end_at)

    by_status = (
        base.with_entities(
            ClientPenalty.status.label("status"),
            func.count(ClientPenalty.id).label("count"),
            func.coalesce(func.sum(ClientPenalty.amount), 0).label("amount"),
            func.coalesce(func.sum(ClientPenalty.points), 0).label("points"),
        )
        .group_by(ClientPenalty.status)
        .all()
    )
    no_show_clients = (
        base.with_entities(
            ClientPenalty.client_id.label("client_id"),
            func.count(ClientPenalty.id).label("no_shows"),
            func.coalesce(func.sum(ClientPenalty.points), 0).label("points"),
        )
        .filter(ClientPenalty.penalty_type == "no_show")
        .group_by(ClientPenalty.client_id)
        .order_by(func.count(ClientPenalty.id).desc())
        .all()
    )
    by_branch = (
        base.join(Appointment, ClientPenalty.appointment_id == Appointment.id)
        .with_entities(
            Appointment.branch_id.label("branch_id"),
            func.count(ClientPenalty.id).label("count"),
            func.coalesce(func.sum(ClientPenalty.amount), 0).label("amount"),
            func.coalesce(func.sum(ClientPenalty.points), 0).label("points"),
        )
        .group_by(Appointment.branch_id)
        .all()
    )
    return {
        "by_status": [
            {
                "status": row.status,
                "count": row.count,
                "amount": float(row.amount or 0),
                "points": int(row.points or 0),
            }
            for row in by_status
        ],
        "top_no_show_clients": [
            {
                "client_id": row.client_id,
                "no_shows": row.no_shows,
                "points": int(row.points or 0),
            }
            for row in no_show_clients
        ],
        "by_branch": [
            {
                "branch_id": row.branch_id,
                "count": row.count,
                "amount": float(row.amount or 0),
                "points": int(row.points or 0),
            }
            for row in by_branch
        ],
    }
