from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.payment import (
    PaymentCreate,
    PaymentMarkPaid,
    PaymentRefund,
    PaymentResponse,
    PaymentSummaryResponse,
)
from app.services.payment_service import (
    create_payment,
    get_payment,
    get_summary,
    list_payments_for_appointment,
    mark_payment_paid,
    refund_payment,
)


router = APIRouter()


@router.post(
    "/",
    response_model=PaymentResponse,
    summary="Registrar pago o deposito",
    description="Registra un pago interno para una cita activa y actualiza el estado de pago agregado de la cita.",
)
def create_payment_api(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_payment(db, data, current_user)


@router.get(
    "/summary",
    response_model=PaymentSummaryResponse,
    summary="Resumen de pagos",
    description="Devuelve totales de pagos y reembolsos por moneda. Requiere rol admin.",
)
def payment_summary_api(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    currency: str = Query(default="DOP", min_length=3, max_length=3),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_summary(db, current_user, start_date, end_date, currency)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Obtener pago",
    description="Obtiene un pago por ID. Admin puede ver todos; barbero solo pagos de sus citas.",
)
def get_payment_api(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_payment(db, payment_id, current_user)


@router.get(
    "/appointment/{appointment_id}",
    response_model=list[PaymentResponse],
    summary="Listar pagos de una cita",
    description="Lista pagos asociados a una cita respetando permisos por rol.",
)
def get_appointment_payments_api(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_payments_for_appointment(db, appointment_id, current_user)


@router.patch(
    "/{payment_id}/mark-paid",
    response_model=PaymentResponse,
    summary="Marcar pago como cobrado",
    description="Convierte un pago pendiente en cobrado, asigna fecha de pago y recalcula el estado de pago de la cita.",
)
def mark_payment_paid_api(
    payment_id: int,
    data: PaymentMarkPaid | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return mark_payment_paid(db, payment_id, data or PaymentMarkPaid(), current_user)


@router.patch(
    "/{payment_id}/refund",
    response_model=PaymentResponse,
    summary="Reembolsar pago",
    description="Marca un pago cobrado como reembolsado, guarda el motivo y registra el cambio en historial de cita.",
)
def refund_payment_api(
    payment_id: int,
    data: PaymentRefund,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return refund_payment(db, payment_id, data, current_user)
