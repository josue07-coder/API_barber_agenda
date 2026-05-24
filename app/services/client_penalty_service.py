from datetime import date, datetime, time, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.client_penalty import ClientPenalty
from app.models.user import User
from app.repositories.appointment_repo import get_appointment_by_id
from app.repositories.client_penalty_repo import (
    create_penalty,
    get_active_penalty_points,
    get_penalties_by_client,
    get_penalties_for_barber,
    get_penalty_by_appointment_and_type,
    get_penalty_by_id,
    penalty_report,
    update_penalty,
)
from app.repositories.client_repo import get_client_by_id
from app.schema.client_penalty import ClientPenaltyCreate, PenaltyResolution
from app.services.branch_service import get_effective_branch_settings
from app.services.notification_service import create_internal_notification


def penalty_amount(value: Decimal | float | int | None) -> Decimal | None:
    if value is None:
        return None
    amount = Decimal(str(value))
    return amount if amount > 0 else None


def no_show_config(db: Session, appointment: Appointment) -> tuple[int, Decimal | None]:
    branch_settings = get_effective_branch_settings(db, appointment.branch_id)
    if branch_settings:
        return branch_settings.no_show_penalty_points, penalty_amount(branch_settings.no_show_penalty_amount)
    return settings.CLIENT_NO_SHOW_PENALTY_POINTS, penalty_amount(settings.CLIENT_NO_SHOW_PENALTY_AMOUNT)


def late_cancel_config(db: Session, appointment: Appointment) -> tuple[int, Decimal | None]:
    branch_settings = get_effective_branch_settings(db, appointment.branch_id)
    if branch_settings:
        return branch_settings.late_cancel_penalty_points, penalty_amount(branch_settings.late_cancel_penalty_amount)
    return settings.CLIENT_LATE_CANCEL_PENALTY_POINTS, penalty_amount(settings.CLIENT_LATE_CANCEL_PENALTY_AMOUNT)


def ensure_can_access_client_penalties(db: Session, current_user: User, client_id: int) -> None:
    if current_user.role == "admin":
        return

    if current_user.role == "client" and current_user.client_id == client_id:
        return

    if current_user.role == "barber":
        penalties = get_penalties_by_client(db, client_id)
        if any(
            penalty.appointment
            and (
                penalty.appointment.user_id == current_user.id
                or (
                    current_user.branch_id is not None
                    and penalty.appointment.branch_id == current_user.branch_id
                )
            )
            for penalty in penalties
        ):
            return

    raise HTTPException(403, "No tienes permiso para acceder a estas penalizaciones")


def ensure_can_access_penalty(db: Session, current_user: User, penalty: ClientPenalty) -> None:
    ensure_can_access_client_penalties(db, current_user, penalty.client_id)


def list_client_penalties(db: Session, client_id: int, current_user: User) -> list[ClientPenalty]:
    if not get_client_by_id(db, client_id):
        raise HTTPException(404, "Cliente no encontrado")
    ensure_can_access_client_penalties(db, current_user, client_id)
    return get_penalties_by_client(db, client_id)


def list_my_penalties(db: Session, current_user: User) -> list[ClientPenalty]:
    if current_user.role != "client" or current_user.client_id is None:
        raise HTTPException(403, "Usuario cliente requerido")
    return get_penalties_by_client(db, current_user.client_id)


def create_manual_penalty(
    db: Session,
    client_id: int,
    data: ClientPenaltyCreate,
    current_user: User,
) -> ClientPenalty:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")
    if not get_client_by_id(db, client_id):
        raise HTTPException(404, "Cliente no encontrado")

    appointment = None
    if data.appointment_id is not None:
        appointment = get_appointment_by_id(db, data.appointment_id)
        if not appointment or appointment.client_id != client_id:
            raise HTTPException(404, "Cita no encontrada para este cliente")

    return create_penalty(
        db,
        ClientPenalty(
            client_id=client_id,
            appointment_id=appointment.id if appointment else None,
            penalty_type=data.penalty_type,
            reason=data.reason,
            amount=data.amount,
            points=data.points,
            status="active",
            created_by_user_id=current_user.id,
        ),
    )


def create_automatic_penalty(
    db: Session,
    *,
    appointment: Appointment,
    penalty_type: str,
    reason: str,
    created_by_user_id: int,
    points: int,
    amount: Decimal | None,
) -> ClientPenalty | None:
    if points <= 0 and not amount:
        return None

    existing = get_penalty_by_appointment_and_type(db, appointment.id, penalty_type)
    if existing:
        return existing

    penalty = create_penalty(
        db,
        ClientPenalty(
            client_id=appointment.client_id,
            appointment_id=appointment.id,
            penalty_type=penalty_type,
            reason=reason,
            amount=amount,
            points=points,
            status="active",
            created_by_user_id=created_by_user_id,
        ),
    )
    create_internal_notification(
        db,
        recipient_type="client",
        recipient_id=appointment.client_id,
        subject=f"client_penalty_{penalty_type}",
        message=f"Penalizacion {penalty_type}: {reason}",
        related_type="penalty",
        related_id=penalty.id,
    )
    return penalty


def register_no_show_penalty(db: Session, appointment: Appointment, current_user: User) -> ClientPenalty | None:
    points, amount = no_show_config(db, appointment)
    return create_automatic_penalty(
        db,
        appointment=appointment,
        penalty_type="no_show",
        reason="No asistencia a la cita",
        created_by_user_id=current_user.id,
        points=points,
        amount=amount,
    )


def register_late_cancel_penalty(db: Session, appointment: Appointment, current_user: User) -> ClientPenalty | None:
    points, amount = late_cancel_config(db, appointment)
    return create_automatic_penalty(
        db,
        appointment=appointment,
        penalty_type="late_cancel",
        reason="Cancelacion tardia dentro de la ventana de corte",
        created_by_user_id=current_user.id,
        points=points,
        amount=amount,
    )


def enforce_client_booking_reputation(db: Session, client_id: int) -> None:
    if not settings.CLIENT_BLOCK_BOOKING_ON_PENALTY:
        return

    active_points = get_active_penalty_points(db, client_id)
    if active_points > settings.CLIENT_MAX_ACTIVE_PENALTY_POINTS:
        raise HTTPException(
            403,
            f"El cliente tiene {active_points} puntos activos de penalizacion y no puede reservar",
        )


def get_penalty_or_404(db: Session, penalty_id: int) -> ClientPenalty:
    penalty = get_penalty_by_id(db, penalty_id)
    if not penalty:
        raise HTTPException(404, "Penalizacion no encontrada")
    return penalty


def forgive_penalty(
    db: Session,
    penalty_id: int,
    data: PenaltyResolution,
    current_user: User,
) -> ClientPenalty:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")
    penalty = get_penalty_or_404(db, penalty_id)
    penalty.status = "forgiven"
    penalty.forgiven_by_user_id = current_user.id
    penalty.resolved_at = datetime.now(timezone.utc)
    if data.reason:
        penalty.reason = data.reason
    return update_penalty(db, penalty)


def mark_penalty_paid(
    db: Session,
    penalty_id: int,
    data: PenaltyResolution,
    current_user: User,
) -> ClientPenalty:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")
    penalty = get_penalty_or_404(db, penalty_id)
    penalty.status = "paid"
    penalty.resolved_at = datetime.now(timezone.utc)
    if data.reason:
        penalty.reason = data.reason
    return update_penalty(db, penalty)


def cancel_penalty(
    db: Session,
    penalty_id: int,
    data: PenaltyResolution,
    current_user: User,
) -> ClientPenalty:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")
    penalty = get_penalty_or_404(db, penalty_id)
    penalty.status = "cancelled"
    penalty.resolved_at = datetime.now(timezone.utc)
    if data.reason:
        penalty.reason = data.reason
    return update_penalty(db, penalty)


def get_penalties_for_current_barber(db: Session, current_user: User) -> list[ClientPenalty]:
    if current_user.role != "barber":
        raise HTTPException(403, "No tienes permiso")
    return get_penalties_for_barber(db, current_user.id)


def get_penalty_report(
    db: Session,
    current_user: User,
    start_date: date,
    end_date: date,
) -> dict:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")
    if start_date > end_date:
        raise HTTPException(400, "Rango de fechas invalido")
    start_at = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_at = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return penalty_report(db, start_at, end_at)
