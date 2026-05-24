from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.barber_commission import BarberCommission
from app.models.barber_commission_rule import BarberCommissionRule


def create_rule(db: Session, rule: BarberCommissionRule) -> BarberCommissionRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def get_rule_by_id(db: Session, rule_id: int) -> BarberCommissionRule | None:
    return db.query(BarberCommissionRule).filter(BarberCommissionRule.id == rule_id).first()


def get_rules(db: Session, barber_id: int | None = None) -> list[BarberCommissionRule]:
    query = db.query(BarberCommissionRule)
    if barber_id is not None:
        query = query.filter(BarberCommissionRule.barber_id == barber_id)
    return query.order_by(BarberCommissionRule.id.desc()).all()


def update_rule(db: Session, rule: BarberCommissionRule) -> BarberCommissionRule:
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def find_active_rules(
    db: Session,
    *,
    barber_id: int,
    branch_id: int | None,
    service_id: int,
    at: datetime,
) -> list[BarberCommissionRule]:
    return (
        db.query(BarberCommissionRule)
        .filter(
            BarberCommissionRule.barber_id == barber_id,
            BarberCommissionRule.is_active == True,
            (BarberCommissionRule.starts_at.is_(None) | (BarberCommissionRule.starts_at <= at)),
            (BarberCommissionRule.ends_at.is_(None) | (BarberCommissionRule.ends_at >= at)),
        )
        .filter(
            (
                (BarberCommissionRule.service_id == service_id)
                | (BarberCommissionRule.service_id.is_(None))
            )
        )
        .filter(
            (
                (BarberCommissionRule.branch_id == branch_id)
                | (BarberCommissionRule.branch_id.is_(None))
            )
        )
        .all()
    )


def create_commission(db: Session, commission: BarberCommission) -> BarberCommission:
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


def get_commission_by_id(db: Session, commission_id: int) -> BarberCommission | None:
    return db.query(BarberCommission).filter(BarberCommission.id == commission_id).first()


def get_commission_by_payment(db: Session, payment_id: int) -> BarberCommission | None:
    return db.query(BarberCommission).filter(BarberCommission.payment_id == payment_id).first()


def get_commissions(
    db: Session,
    barber_id: int | None = None,
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[BarberCommission]:
    query = db.query(BarberCommission)
    if barber_id is not None:
        query = query.filter(BarberCommission.barber_id == barber_id)
    if status is not None:
        query = query.filter(BarberCommission.status == status)
    if start_date is not None:
        query = query.filter(BarberCommission.calculated_at >= start_date)
    if end_date is not None:
        query = query.filter(BarberCommission.calculated_at <= end_date)
    return query.order_by(BarberCommission.calculated_at.desc(), BarberCommission.id.desc()).all()


def update_commission(db: Session, commission: BarberCommission) -> BarberCommission:
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


def _apply_commission_date_filter(query, start_date: datetime | None, end_date: datetime | None):
    if start_date is not None:
        query = query.filter(BarberCommission.calculated_at >= start_date)
    if end_date is not None:
        query = query.filter(BarberCommission.calculated_at <= end_date)
    return query


def commission_summary(db: Session, start_date: datetime | None = None, end_date: datetime | None = None):
    query = db.query(
        BarberCommission.status.label("status"),
        func.count(BarberCommission.id).label("count"),
        func.coalesce(func.sum(BarberCommission.commission_amount), 0).label("total"),
    )
    query = _apply_commission_date_filter(query, start_date, end_date)
    return (
        query
        .group_by(BarberCommission.status)
        .all()
    )


def commission_totals_by_barber(db: Session, start_date: datetime | None = None, end_date: datetime | None = None):
    query = db.query(
        BarberCommission.barber_id.label("barber_id"),
        func.coalesce(func.sum(BarberCommission.commission_amount), 0).label("total"),
    )
    query = _apply_commission_date_filter(query, start_date, end_date)
    return (
        query
        .filter(BarberCommission.status != "cancelled")
        .group_by(BarberCommission.barber_id)
        .all()
    )


def commission_totals_by_branch(db: Session, start_date: datetime | None = None, end_date: datetime | None = None):
    query = db.query(
        BarberCommission.branch_id.label("branch_id"),
        func.coalesce(func.sum(BarberCommission.commission_amount), 0).label("total"),
    )
    query = _apply_commission_date_filter(query, start_date, end_date)
    return (
        query
        .filter(BarberCommission.status != "cancelled")
        .group_by(BarberCommission.branch_id)
        .all()
    )
