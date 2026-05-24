from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.barber_commission import BarberCommission
from app.models.barber_commission_rule import BarberCommissionRule
from app.models.payment import Payment
from app.models.user import User
from app.repositories.commission_repo import (
    commission_summary,
    commission_totals_by_barber,
    commission_totals_by_branch,
    create_commission,
    create_rule,
    find_active_rules,
    get_commission_by_id,
    get_commission_by_payment,
    get_commissions,
    get_rule_by_id,
    get_rules,
    update_commission,
    update_rule,
)
from app.repositories.service_repo import get_service_by_id
from app.repositories.user_repo import get_user_by_id
from app.services.branch_service import get_active_branch_or_404
from app.schema.commission import CommissionRuleCreate, CommissionRuleUpdate


def ensure_admin(current_user: User) -> None:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")


def validate_rule_entities(db: Session, barber_id: int, branch_id: int | None, service_id: int | None):
    barber = get_user_by_id(db, barber_id)
    if not barber or barber.role != "barber" or not barber.is_active:
        raise HTTPException(404, "Barbero no encontrado")
    if branch_id is not None:
        get_active_branch_or_404(db, branch_id)
        if barber.branch_id is not None and barber.branch_id != branch_id:
            raise HTTPException(400, "El barbero no pertenece a la sucursal seleccionada")
    if service_id is not None:
        service = get_service_by_id(db, service_id)
        if not service or not service.is_active:
            raise HTTPException(404, "Servicio no encontrado")
        if branch_id is not None and service.branch_id is not None and service.branch_id != branch_id:
            raise HTTPException(400, "El servicio no pertenece a la sucursal seleccionada")


def create_commission_rule(db: Session, data: CommissionRuleCreate, current_user: User):
    ensure_admin(current_user)
    validate_rule_entities(db, data.barber_id, data.branch_id, data.service_id)
    return create_rule(
        db,
        BarberCommissionRule(
            barber_id=data.barber_id,
            branch_id=data.branch_id,
            service_id=data.service_id,
            commission_type=data.commission_type,
            commission_value=data.commission_value,
            is_active=True,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
        ),
    )


def list_commission_rules(db: Session, current_user: User):
    if current_user.role == "admin":
        return get_rules(db)
    if current_user.role == "barber":
        return get_rules(db, barber_id=current_user.id)
    raise HTTPException(403, "No tienes permiso")


def update_commission_rule(db: Session, rule_id: int, data: CommissionRuleUpdate, current_user: User):
    ensure_admin(current_user)
    rule = get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(404, "Regla no encontrada")
    branch_id = data.branch_id if data.branch_id is not None else rule.branch_id
    service_id = data.service_id if data.service_id is not None else rule.service_id
    validate_rule_entities(db, rule.barber_id, branch_id, service_id)
    if data.branch_id is not None:
        rule.branch_id = data.branch_id
    if data.service_id is not None:
        rule.service_id = data.service_id
    if data.commission_type is not None:
        rule.commission_type = data.commission_type
    if data.commission_value is not None:
        rule.commission_value = data.commission_value
    if data.is_active is not None:
        rule.is_active = data.is_active
    if data.starts_at is not None:
        rule.starts_at = data.starts_at
    if data.ends_at is not None:
        rule.ends_at = data.ends_at
    return update_rule(db, rule)


def deactivate_commission_rule(db: Session, rule_id: int, current_user: User):
    ensure_admin(current_user)
    rule = get_rule_by_id(db, rule_id)
    if not rule:
        raise HTTPException(404, "Regla no encontrada")
    rule.is_active = False
    return update_rule(db, rule)


def rule_priority(rule: BarberCommissionRule, service_id: int, branch_id: int | None) -> int:
    if rule.service_id == service_id:
        return 3
    if rule.branch_id == branch_id:
        return 2
    return 1


def select_rule(db: Session, payment: Payment):
    appointment = payment.appointment
    rules = find_active_rules(
        db,
        barber_id=appointment.user_id,
        branch_id=appointment.branch_id,
        service_id=appointment.service_id,
        at=datetime.now(timezone.utc),
    )
    if not rules:
        return None
    return sorted(
        rules,
        key=lambda rule: (rule_priority(rule, appointment.service_id, appointment.branch_id), rule.id),
        reverse=True,
    )[0]


def calculate_commission(rule: BarberCommissionRule, base_amount: Decimal) -> Decimal:
    if rule.commission_type == "percentage":
        return (Decimal(base_amount) * Decimal(rule.commission_value)) / Decimal("100")
    return Decimal(rule.commission_value)


def generate_commission_for_payment(db: Session, payment: Payment) -> BarberCommission | None:
    if get_commission_by_payment(db, payment.id):
        return None

    if payment.status not in {"paid", "partially_paid"}:
        return None

    rule = select_rule(db, payment)
    if not rule:
        return None

    appointment = payment.appointment
    commission = BarberCommission(
        appointment_id=appointment.id,
        payment_id=payment.id,
        barber_id=appointment.user_id,
        branch_id=appointment.branch_id,
        service_id=appointment.service_id,
        base_amount=payment.amount,
        commission_amount=calculate_commission(rule, payment.amount),
        status="pending",
        notes=f"Regla #{rule.id}",
    )
    try:
        return create_commission(db, commission)
    except IntegrityError:
        db.rollback()
        return None


def cancel_commission_for_payment(db: Session, payment: Payment):
    commission = get_commission_by_payment(db, payment.id)
    if not commission:
        return None
    commission.status = "cancelled"
    commission.notes = "Cancelada por reembolso"
    return update_commission(db, commission)


def list_commissions(db: Session, current_user: User, status: str | None = None):
    if current_user.role == "admin":
        return get_commissions(db, status=status)
    if current_user.role == "barber":
        return get_commissions(db, barber_id=current_user.id, status=status)
    raise HTTPException(403, "No tienes permiso")


def list_commissions_by_barber(db: Session, barber_id: int, current_user: User):
    if current_user.role == "barber" and current_user.id != barber_id:
        raise HTTPException(403, "No tienes permiso")
    if current_user.role not in {"admin", "barber"}:
        raise HTTPException(403, "No tienes permiso")
    return get_commissions(db, barber_id=barber_id)


def get_commission_or_404(db: Session, commission_id: int):
    commission = get_commission_by_id(db, commission_id)
    if not commission:
        raise HTTPException(404, "Comision no encontrada")
    return commission


def approve_commission(db: Session, commission_id: int, current_user: User):
    ensure_admin(current_user)
    commission = get_commission_or_404(db, commission_id)
    if commission.status != "pending":
        raise HTTPException(400, "Solo se pueden aprobar comisiones pendientes")
    commission.status = "approved"
    commission.approved_by_user_id = current_user.id
    return update_commission(db, commission)


def mark_commission_paid(db: Session, commission_id: int, current_user: User):
    ensure_admin(current_user)
    commission = get_commission_or_404(db, commission_id)
    if commission.status not in {"pending", "approved"}:
        raise HTTPException(400, "La comision no puede marcarse como pagada")
    commission.status = "paid"
    commission.approved_by_user_id = commission.approved_by_user_id or current_user.id
    commission.paid_at = datetime.now(timezone.utc)
    return update_commission(db, commission)


def get_commission_summary(db: Session, current_user: User):
    ensure_admin(current_user)
    by_status = {
        row.status: {
            "count": row.count,
            "total": float(row.total),
        }
        for row in commission_summary(db)
    }
    return {
        "by_status": by_status,
        "by_barber": [
            {"barber_id": row.barber_id, "total": float(row.total)}
            for row in commission_totals_by_barber(db)
        ],
        "by_branch": [
            {"branch_id": row.branch_id, "total": float(row.total)}
            for row in commission_totals_by_branch(db)
        ],
    }


def get_commission_summary_by_range(
    db: Session,
    current_user: User,
    start_date: date | None = None,
    end_date: date | None = None,
):
    ensure_admin(current_user)
    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, "Rango de fechas invalido")

    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc) if start_date else None
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc) if end_date else None

    by_status = {
        row.status: {
            "count": row.count,
            "total": float(row.total),
        }
        for row in commission_summary(db, start_dt, end_dt)
    }
    return {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "by_status": by_status,
        "by_barber": [
            {"barber_id": row.barber_id, "total": float(row.total)}
            for row in commission_totals_by_barber(db, start_dt, end_dt)
        ],
        "by_branch": [
            {"branch_id": row.branch_id, "total": float(row.total)}
            for row in commission_totals_by_branch(db, start_dt, end_dt)
        ],
    }
