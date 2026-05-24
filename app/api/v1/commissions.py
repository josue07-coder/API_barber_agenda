from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.commission import (
    CommissionResponse,
    CommissionRuleCreate,
    CommissionRuleResponse,
    CommissionRuleUpdate,
)
from app.services.commission_service import (
    approve_commission,
    create_commission_rule,
    deactivate_commission_rule,
    get_commission_summary_by_range,
    list_commission_rules,
    list_commissions,
    list_commissions_by_barber,
    mark_commission_paid,
    update_commission_rule,
)


router = APIRouter()


@router.post(
    "/rules",
    response_model=CommissionRuleResponse,
    summary="Crear regla de comision",
    description="Crea una regla activa de comision para un barbero, opcionalmente acotada por sucursal o servicio. Requiere admin.",
)
def create_rule_api(
    data: CommissionRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_commission_rule(db, data, current_user)


@router.get(
    "/rules",
    response_model=list[CommissionRuleResponse],
    summary="Listar reglas de comision",
    description="Admin ve todas las reglas; barber puede ver sus reglas propias.",
)
def list_rules_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_commission_rules(db, current_user)


@router.put(
    "/rules/{rule_id}",
    response_model=CommissionRuleResponse,
    summary="Actualizar regla de comision",
    description="Actualiza tipo, valor, sucursal, servicio o vigencia de una regla. Requiere admin.",
)
def update_rule_api(
    rule_id: int,
    data: CommissionRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_commission_rule(db, rule_id, data, current_user)


@router.patch(
    "/rules/{rule_id}/deactivate",
    response_model=CommissionRuleResponse,
    summary="Desactivar regla de comision",
    description="Desactiva una regla de comision sin eliminar historico. Requiere admin.",
)
def deactivate_rule_api(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deactivate_commission_rule(db, rule_id, current_user)


@router.get(
    "/summary",
    summary="Resumen de comisiones",
    description="Resume comisiones por estado, barbero y sucursal. Requiere admin.",
)
def commission_summary_api(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_commission_summary_by_range(db, current_user, start_date, end_date)


@router.get(
    "/",
    response_model=list[CommissionResponse],
    summary="Listar comisiones",
    description="Admin ve todas las comisiones; barber solo sus propias comisiones.",
)
def list_commissions_api(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_commissions(db, current_user, status)


@router.get(
    "/barber/{barber_id}",
    response_model=list[CommissionResponse],
    summary="Listar comisiones por barbero",
    description="Admin puede consultar cualquier barbero; barber solo puede consultar sus propias comisiones.",
)
def list_barber_commissions_api(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_commissions_by_barber(db, barber_id, current_user)


@router.patch(
    "/{commission_id}/approve",
    response_model=CommissionResponse,
    summary="Aprobar comision",
    description="Marca una comision pendiente como aprobada. Requiere admin.",
)
def approve_commission_api(
    commission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return approve_commission(db, commission_id, current_user)


@router.patch(
    "/{commission_id}/mark-paid",
    response_model=CommissionResponse,
    summary="Marcar comision como pagada",
    description="Marca una comision pendiente o aprobada como pagada. Requiere admin.",
)
def mark_commission_paid_api(
    commission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return mark_commission_paid(db, commission_id, current_user)
