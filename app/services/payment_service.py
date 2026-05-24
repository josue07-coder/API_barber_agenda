from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.payment_status import PaymentStatus
from app.models.user import User
from app.repositories.appointment_repo import get_appointment_by_id, update_appointment
from app.repositories.payment_repo import (
    create_payment as repo_create_payment,
    get_payment_by_id,
    get_payment_summary,
    get_payments_by_appointment,
    get_payments_by_client,
    get_total_paid_for_appointment,
    update_payment,
)
from app.repositories.service_repo import get_service_by_id
from app.schema.payment import PaymentCreate, PaymentMarkPaid, PaymentRefund
from app.services.branch_service import get_effective_branch_settings
from app.services.appointment_service import (
    appointment_snapshot,
    record_appointment_history,
)
from app.services.notification_service import notify_payment_event
from app.services.cash_register_service import create_payment_cash_movement
from app.services.commission_service import (
    cancel_commission_for_payment,
    generate_commission_for_payment,
)


def ensure_can_access_payment_appointment(user: User, appointment) -> None:
    if user.role == "admin":
        return

    if user.role == "barber" and appointment.user_id == user.id:
        return

    if user.role == "client" and user.client_id == appointment.client_id:
        return

    raise HTTPException(403, "No tienes permiso para acceder a este pago")


def get_payment_or_404(db: Session, payment_id: int) -> Payment:
    payment = get_payment_by_id(db, payment_id)
    if not payment:
        raise HTTPException(404, "Pago no encontrado")
    return payment


def update_appointment_payment_status(db: Session, appointment) -> None:
    service = get_service_by_id(db, appointment.service_id)
    if not service:
        appointment.payment_status = PaymentStatus.pending.value
        update_appointment(db, appointment)
        return

    total_paid = get_total_paid_for_appointment(db, appointment.id)

    if total_paid <= 0:
        payments = get_payments_by_appointment(db, appointment.id)
        if payments and all(payment.status == PaymentStatus.refunded.value for payment in payments):
            appointment.payment_status = PaymentStatus.refunded.value
        else:
            appointment.payment_status = PaymentStatus.pending.value
    elif total_paid >= service.price:
        appointment.payment_status = PaymentStatus.paid.value
    else:
        appointment.payment_status = PaymentStatus.partially_paid.value

    update_appointment(db, appointment)


def expected_deposit_amount(db: Session, appointment) -> float:
    branch_settings = get_effective_branch_settings(db, appointment.branch_id)
    if not branch_settings or not branch_settings.deposit_required:
        return 0.0

    if branch_settings.default_deposit_amount is not None:
        return float(branch_settings.default_deposit_amount)

    if branch_settings.default_deposit_percentage is not None:
        service = get_service_by_id(db, appointment.service_id)
        if not service:
            return 0.0
        return float(service.price) * float(branch_settings.default_deposit_percentage) / 100

    return 0.0


def create_payment(db: Session, data: PaymentCreate, current_user: User) -> Payment:
    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso para registrar pagos")

    appointment = get_appointment_by_id(db, data.appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_payment_appointment(current_user, appointment)

    if appointment.status == "cancelada":
        raise HTTPException(400, "No se pueden registrar pagos en una cita cancelada")

    branch_settings = get_effective_branch_settings(db, appointment.branch_id)
    expected_deposit = expected_deposit_amount(db, appointment)
    if expected_deposit and float(data.amount) < expected_deposit:
        raise HTTPException(400, f"El deposito minimo requerido es {expected_deposit:.2f}")

    payment = Payment(
        appointment_id=appointment.id,
        client_id=appointment.client_id,
        amount=data.amount,
        currency=(branch_settings.currency if branch_settings else data.currency).upper(),
        payment_method=data.payment_method.value,
        status=data.status.value,
        transaction_reference=data.transaction_reference,
        notes=data.notes,
        paid_at=datetime.now(timezone.utc)
        if data.status in {PaymentStatus.paid, PaymentStatus.partially_paid}
        else None,
    )

    try:
        payment = repo_create_payment(db, payment)
    except IntegrityError:
        raise HTTPException(409, "No se pudo registrar el pago")

    if payment.status in {PaymentStatus.paid.value, PaymentStatus.partially_paid.value}:
        old_values = appointment_snapshot(appointment)
        update_appointment_payment_status(db, appointment)
        record_appointment_history(
            db,
            appointment=appointment,
            action="payment_received",
            changed_by_user_id=current_user.id,
            old_values=old_values,
            new_values={
                **appointment_snapshot(appointment),
                "payment_id": payment.id,
                "payment_status": appointment.payment_status,
            },
            reason=payment.notes,
        )
        notify_payment_event(db, payment, "payment_registered")
        create_payment_cash_movement(db, payment, current_user, "income")
        generate_commission_for_payment(db, payment)

    return payment


def get_payment(db: Session, payment_id: int, current_user: User) -> Payment:
    payment = get_payment_or_404(db, payment_id)
    ensure_can_access_payment_appointment(current_user, payment.appointment)
    return payment


def list_payments_for_appointment(
    db: Session,
    appointment_id: int,
    current_user: User,
) -> list[Payment]:
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_payment_appointment(current_user, appointment)
    return get_payments_by_appointment(db, appointment_id)


def list_my_payments(db: Session, current_user: User) -> list[Payment]:
    if current_user.role != "client" or current_user.client_id is None:
        raise HTTPException(403, "Usuario cliente requerido")
    return get_payments_by_client(db, current_user.client_id)


def mark_payment_paid(
    db: Session,
    payment_id: int,
    data: PaymentMarkPaid,
    current_user: User,
) -> Payment:
    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso para modificar pagos")

    payment = get_payment_or_404(db, payment_id)
    appointment = payment.appointment
    ensure_can_access_payment_appointment(current_user, appointment)

    if appointment.status == "cancelada":
        raise HTTPException(400, "No se pueden registrar pagos en una cita cancelada")

    if payment.status == PaymentStatus.refunded.value:
        raise HTTPException(400, "No se puede marcar como pagado un pago reembolsado")

    old_values = appointment_snapshot(appointment)
    payment.status = PaymentStatus.paid.value
    payment.paid_at = payment.paid_at or datetime.now(timezone.utc)
    if data.transaction_reference is not None:
        payment.transaction_reference = data.transaction_reference
    if data.notes is not None:
        payment.notes = data.notes

    payment = update_payment(db, payment)
    update_appointment_payment_status(db, appointment)
    record_appointment_history(
        db,
        appointment=appointment,
        action="payment_received",
        changed_by_user_id=current_user.id,
        old_values=old_values,
        new_values={
            **appointment_snapshot(appointment),
            "payment_id": payment.id,
            "payment_status": appointment.payment_status,
        },
        reason=payment.notes,
    )
    notify_payment_event(db, payment, "payment_registered")
    create_payment_cash_movement(db, payment, current_user, "income")
    generate_commission_for_payment(db, payment)
    return payment


def refund_payment(
    db: Session,
    payment_id: int,
    data: PaymentRefund,
    current_user: User,
) -> Payment:
    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso para reembolsar pagos")

    payment = get_payment_or_404(db, payment_id)
    appointment = payment.appointment
    ensure_can_access_payment_appointment(current_user, appointment)

    if payment.status == PaymentStatus.refunded.value:
        raise HTTPException(400, "El pago ya fue reembolsado")

    if payment.status not in {PaymentStatus.paid.value, PaymentStatus.partially_paid.value}:
        raise HTTPException(400, "Solo se pueden reembolsar pagos cobrados")

    old_values = appointment_snapshot(appointment)
    payment.status = PaymentStatus.refunded.value
    payment.refunded_at = datetime.now(timezone.utc)
    payment.notes = data.reason
    payment = update_payment(db, payment)
    update_appointment_payment_status(db, appointment)
    record_appointment_history(
        db,
        appointment=appointment,
        action="payment_refunded",
        changed_by_user_id=current_user.id,
        old_values=old_values,
        new_values={
            **appointment_snapshot(appointment),
            "payment_id": payment.id,
            "payment_status": appointment.payment_status,
        },
        reason=data.reason,
    )
    notify_payment_event(db, payment, "payment_refunded")
    create_payment_cash_movement(db, payment, current_user, "refund")
    cancel_commission_for_payment(db, payment)
    return payment


def get_summary(
    db: Session,
    current_user: User,
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str = "DOP",
):
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, "Rango de fechas invalido")

    return get_payment_summary(db, start_date, end_date, currency.upper())
