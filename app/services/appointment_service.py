from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime, timedelta, time, date, timezone
from decimal import Decimal
from typing import List, Optional

from app.schema.appointment import AppointmentCreate, AppointmentReschedule
from app.models.user import User
from app.models.appointment_status import AppointmentStatus
from app.models.appointment import Appointment
from app.models.appointment_history import AppointmentHistory
from app.repositories.appointment_history_repo import (
    create_appointment_history,
    get_history_by_appointment,
)
from app.repositories.appointment_repo import (
    get_appointments_by_day,
    get_appointments_by_day_for_update,
    get_appointments_by_barber,
    get_appointments_by_client,
    get_appointment_by_id,
    create_appointment,
    get_appointments,
    update_appointment,
)
from app.core.config import (
    APPOINTMENT_BUFFER_MINUTES,
    NO_SHOW_TOLERANCE_MINUTES,
    settings,
)
from app.repositories.service_repo import get_service_by_id
from app.repositories.user_repo import get_user_by_id
from app.repositories.client_repo import get_client_by_id
from app.utils.time_utils import calculate_end_time
from app.services.branch_service import get_active_branch_or_404, get_effective_branch_settings
from app.services.barber_schedule_service import get_schedule_covering_time
from app.repositories.barber_schedule_repo import get_active_schedules_for_day
from app.services.barber_time_block_service import (
    appointment_is_blocked,
)
from app.services.notification_service import notify_appointment_event
from app.services.client_penalty_service import (
    enforce_client_booking_reputation,
    register_late_cancel_penalty,
    register_no_show_penalty,
)


FINAL_STATES = {"completada", "cancelada", "no_show"}
STATUS_ACTIONS = {
    "confirmada": "confirmed",
    "completada": "completed",
    "cancelada": "cancelled",
    "no_show": "no_show",
}


def json_safe(value):
    if isinstance(value, (date, time, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def appointment_snapshot(appointment: Appointment) -> dict:
    return {
        "id": appointment.id,
        "date": json_safe(appointment.date),
        "start_time": json_safe(appointment.start_time),
        "end_time": json_safe(appointment.end_time),
        "status": appointment.status,
        "user_id": appointment.user_id,
        "client_id": appointment.client_id,
        "service_id": appointment.service_id,
        "cancelled_at": json_safe(appointment.cancelled_at),
        "cancelled_by_user_id": appointment.cancelled_by_user_id,
        "cancellation_reason": appointment.cancellation_reason,
    }


def record_appointment_history(
    db: Session,
    *,
    appointment: Appointment,
    action: str,
    changed_by_user_id: int,
    old_values: dict | None = None,
    new_values: dict | None = None,
    reason: str | None = None,
) -> AppointmentHistory:
    return create_appointment_history(
        db,
        AppointmentHistory(
            appointment_id=appointment.id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            changed_by_user_id=changed_by_user_id,
            reason=reason,
        )
    )


def ensure_can_access_appointment(user: User, appointment: Appointment) -> None:
    if user.role == "admin":
        return

    if user.role == "barber" and appointment.user_id == user.id:
        return

    if user.role == "client" and user.client_id == appointment.client_id:
        return

    raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a esta cita"
    )


def is_time_available(
    appointment_date: date,
    new_start: time,
    new_end: time,
    appointments: List[Appointment]
) -> bool:
    buffer = timedelta(minutes=APPOINTMENT_BUFFER_MINUTES)

    new_start_dt = datetime.combine(appointment_date, new_start)
    new_end_dt = datetime.combine(appointment_date, new_end)

    for appt in appointments:
        appt_start = datetime.combine(
            appointment_date, appt.start_time
        ) - buffer

        appt_end = datetime.combine(
            appointment_date, appt.end_time
        ) + buffer

        if new_start_dt < appt_end and new_end_dt > appt_start:
            return False

    return True


def is_inside_schedule_break(schedule, start_time: time, end_time: time) -> bool:
    if schedule.break_start_time is None or schedule.break_end_time is None:
        return False

    return (
        datetime.combine(date.today(), start_time) < datetime.combine(date.today(), schedule.break_end_time)
        and datetime.combine(date.today(), end_time) > datetime.combine(date.today(), schedule.break_start_time)
    )


def enforce_client_cutoff(
    *,
    current_user: User,
    appointment: Appointment,
    cutoff_hours: int,
    action: str,
) -> None:
    if current_user.role != "client":
        return

    appointment_dt = datetime.combine(appointment.date, appointment.start_time)
    remaining = appointment_dt - datetime.now()

    if remaining < timedelta(hours=cutoff_hours):
        raise HTTPException(
            status_code=409,
            detail=f"No se puede {action} la cita con menos de {cutoff_hours} horas de anticipacion",
        )


def client_cutoff_violated(current_user: User, appointment: Appointment, cutoff_hours: int) -> bool:
    if current_user.role != "client":
        return False
    appointment_dt = datetime.combine(appointment.date, appointment.start_time)
    return appointment_dt - datetime.now() < timedelta(hours=cutoff_hours)


def cancel_cutoff_hours_for_appointment(db: Session, appointment: Appointment) -> int:
    branch_settings = get_effective_branch_settings(db, appointment.branch_id)
    if branch_settings:
        return branch_settings.default_cancel_cutoff_hours
    return settings.CLIENT_CANCEL_CUTOFF_HOURS


def reschedule_cutoff_hours_for_appointment(db: Session, appointment: Appointment) -> int:
    branch_settings = get_effective_branch_settings(db, appointment.branch_id)
    if branch_settings:
        return branch_settings.default_reschedule_cutoff_hours
    return settings.CLIENT_RESCHEDULE_CUTOFF_HOURS


def validate_barber_availability(
    db: Session,
    *,
    barber_id: int,
    appointment_date: date,
    start_time: time,
    end_time: time,
) -> None:
    schedule = get_schedule_covering_time(
        db,
        barber_id=barber_id,
        appointment_date=appointment_date,
        start_time=start_time,
        end_time=end_time,
    )

    if not schedule:
        raise HTTPException(400, "El barbero no trabaja en ese horario")

    if is_inside_schedule_break(schedule, start_time, end_time):
        raise HTTPException(400, "La cita cae dentro del descanso del barbero")

    if appointment_is_blocked(
        db,
        barber_id=barber_id,
        appointment_date=appointment_date,
        start_time=start_time,
        end_time=end_time,
    ):
        raise HTTPException(409, "El horario esta bloqueado")


def create_new_appointment(
    db: Session,
    data: AppointmentCreate,
    current_user: User
) -> Appointment:

    barber = get_user_by_id(db, data.barber_id)
    if not barber:
        raise HTTPException(404, "Barbero no encontrado")

    if not barber.is_active:
        raise HTTPException(404, "Barbero no encontrado")

    if barber.role != "barber":
        raise HTTPException(400, "El usuario seleccionado no es un barbero")

    if current_user.role not in {"admin", "barber", "client"}:
        raise HTTPException(403, "No tienes permiso para crear citas")

    if current_user.role == "barber" and data.barber_id != current_user.id:
        raise HTTPException(403, "No puedes crear citas para otro barbero")

    if current_user.role == "client":
        if current_user.client_id is None:
            raise HTTPException(403, "Usuario cliente sin cliente asociado")
        if data.client_id != current_user.client_id:
            raise HTTPException(403, "No puedes crear citas para otro cliente")

    client = get_client_by_id(db, data.client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    enforce_client_booking_reputation(db, data.client_id)

    service = get_service_by_id(db, data.service_id)
    if not service or not service.is_active:
        raise HTTPException(404, "Servicio no encontrado")

    branch_id = data.branch_id or barber.branch_id or service.branch_id
    if branch_id is not None:
        get_active_branch_or_404(db, branch_id)
        if barber.branch_id is not None and barber.branch_id != branch_id:
            raise HTTPException(400, "El barbero no pertenece a la sucursal seleccionada")
        if service.branch_id is not None and service.branch_id != branch_id:
            raise HTTPException(400, "El servicio no pertenece a la sucursal seleccionada")

    if service.duration_minutes <= 0:
        raise HTTPException(400, "La duracion del servicio no es valida")
    
    client_appointments = get_appointments_by_client(db, data.client_id)

    for appt in client_appointments:
        if (
        appt.date == data.date and
        appt.service_id == data.service_id and
        appt.status not in {"cancelada", "no_show"}
    ):
            raise HTTPException(
                status_code=409,
                detail="El cliente ya tiene una cita con este servicio en esta fecha"
            )

    if data.date < date.today():
        raise HTTPException(400, "No se puede agendar en una fecha pasada")
    
    now = datetime.now().time()

    if data.date == date.today() and data.start_time <= now:
        raise HTTPException(
        status_code=400,
        detail="No se puede agendar una cita en una hora pasada"
    )

    start_time = data.start_time.replace(tzinfo=None)

    end_time = calculate_end_time(
        start_time,
        service.duration_minutes
    )

    validate_barber_availability(
        db,
        barber_id=data.barber_id,
        appointment_date=data.date,
        start_time=start_time,
        end_time=end_time,
    )

    appointments = get_appointments_by_day_for_update(
        db,
        data.barber_id,
        data.date
    )

    if not is_time_available(
        data.date,
        start_time,
        end_time,
        appointments
    ):
        raise HTTPException(409, "Horario no disponible")

    appointment = Appointment(
        user_id=data.barber_id,
        client_id=data.client_id,
        service_id=data.service_id,
        branch_id=branch_id,
        date=data.date,
        start_time=start_time,
        end_time=end_time,
        status="agendada"
    )

    try:
        appointment = create_appointment(db, appointment)
    except IntegrityError:
        raise HTTPException(409, "Horario no disponible")

    record_appointment_history(
        db,
        appointment=appointment,
        action="created",
        changed_by_user_id=current_user.id,
        old_values=None,
        new_values=appointment_snapshot(appointment),
    )
    notify_appointment_event(db, appointment, "appointment_created")
    return appointment


def list_all_appointments(
    db: Session,
    current_user: User,
    barber_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    client_id: Optional[int] = None,
    appointment_date: Optional[date] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    if current_user.role != "admin":
        raise HTTPException(403, "Solo administradores")

    return get_appointments(
        db,
        barber_id=barber_id,
        branch_id=branch_id,
        client_id=client_id,
        appointment_date=appointment_date,
        status=status,
        skip=skip,
        limit=limit
    )


def update_existing_appointment(
    db: Session,
    appointment_id: int,
    data: dict,
    current_user: User
) -> Appointment:

    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_appointment(current_user, appointment)

    appointment_dt = datetime.combine(
        appointment.date,
        appointment.start_time
    )

    if datetime.now() >= appointment_dt:
        raise HTTPException(
            400,
            "No se puede modificar una cita que ya inició"
        )

    if appointment.status in FINAL_STATES:
        raise HTTPException(
            400,
            "No se puede modificar una cita cerrada"
        )

    allowed_fields = {"date", "start_time", "status"}
    data = {k: v for k, v in data.items() if k in allowed_fields}

    service = get_service_by_id(db, appointment.service_id)

    if "date" in data or "start_time" in data:
        enforce_client_cutoff(
            current_user=current_user,
            appointment=appointment,
            cutoff_hours=reschedule_cutoff_hours_for_appointment(db, appointment),
            action="reprogramar",
        )

        new_date = data.get("date", appointment.date)

        new_start = data.get(
            "start_time",
            appointment.start_time
        ).replace(tzinfo=None)

        new_end = calculate_end_time(
            new_start,
            service.duration_minutes
        )

        validate_barber_availability(
            db,
            barber_id=appointment.user_id,
            appointment_date=new_date,
            start_time=new_start,
            end_time=new_end,
        )

        appointments = get_appointments_by_day(
            db,
            appointment.user_id,
            new_date
        )

        appointments = [
            appt for appt in appointments
            if appt.id != appointment.id
        ]

        if not is_time_available(
            new_date,
            new_start,
            new_end,
            appointments
        ):
            raise HTTPException(409, "Horario no disponible")

        appointment.date = new_date
        appointment.start_time = new_start
        appointment.end_time = new_end

    if "status" in data:
        if not isinstance(data["status"], AppointmentStatus):
            raise HTTPException(400, "Estado inválido")

        appointment.status = data["status"].value

    try:
        appointment = update_appointment(db, appointment)
    except IntegrityError:
        raise HTTPException(409, "Horario no disponible")

    return appointment



def list_appointments_by_barber(db: Session, barber_id: int):
    return get_appointments_by_barber(db, barber_id)


def list_appointments_by_client(db: Session, client_id: int):
    return get_appointments_by_client(db, client_id)


def list_my_appointments(db: Session, current_user: User):
    if current_user.role != "client" or current_user.client_id is None:
        raise HTTPException(403, "Usuario cliente requerido")
    return get_appointments_by_client(db, current_user.client_id)


def list_appointments_by_day(db: Session, barber_id: int, appointment_date: date):
    return get_appointments_by_day(db, barber_id, appointment_date)


def cancel_appointment(
    db: Session,
    appointment_id: int,
    current_user: User,
    reason: str | None = None,
):
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_appointment(current_user, appointment)

    if appointment.status == "completada":
        raise HTTPException(400, "No se puede cancelar una cita completada")

    if appointment.status == "cancelada":
        raise HTTPException(400, "La cita ya esta cancelada")

    if appointment.status == "no_show":
        raise HTTPException(400, "No se puede cancelar una cita cerrada")

    cancel_cutoff_hours = cancel_cutoff_hours_for_appointment(db, appointment)
    if client_cutoff_violated(current_user, appointment, cancel_cutoff_hours):
        register_late_cancel_penalty(db, appointment, current_user)
        raise HTTPException(
            409,
            f"No se puede cancelar la cita con menos de {cancel_cutoff_hours} horas de anticipacion",
        )

    old_values = appointment_snapshot(appointment)
    appointment.status = "cancelada"
    appointment.cancelled_at = datetime.now(timezone.utc)
    appointment.cancelled_by_user_id = current_user.id
    appointment.cancellation_reason = reason
    appointment = update_appointment(db, appointment)
    record_appointment_history(
        db,
        appointment=appointment,
        action="cancelled",
        changed_by_user_id=current_user.id,
        old_values=old_values,
        new_values=appointment_snapshot(appointment),
        reason=reason,
    )
    notify_appointment_event(db, appointment, "appointment_cancelled")
    return appointment


def reschedule_appointment(
    db: Session,
    appointment_id: int,
    data: AppointmentReschedule,
    current_user: User,
    reason: str | None = None,
) -> Appointment:
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_appointment(current_user, appointment)

    if appointment.status in FINAL_STATES:
        raise HTTPException(400, "No se puede reprogramar una cita cerrada")

    enforce_client_cutoff(
        current_user=current_user,
        appointment=appointment,
        cutoff_hours=reschedule_cutoff_hours_for_appointment(db, appointment),
        action="reprogramar",
    )

    if data.date < date.today():
        raise HTTPException(400, "No se puede reprogramar en una fecha pasada")

    if data.date == date.today() and data.start_time <= datetime.now().time():
        raise HTTPException(400, "No se puede reprogramar en una hora pasada")

    service = get_service_by_id(db, appointment.service_id)
    if not service or not service.is_active:
        raise HTTPException(404, "Servicio no encontrado")

    new_start = data.start_time.replace(tzinfo=None)
    new_end = calculate_end_time(new_start, service.duration_minutes)

    validate_barber_availability(
        db,
        barber_id=appointment.user_id,
        appointment_date=data.date,
        start_time=new_start,
        end_time=new_end,
    )

    appointments = get_appointments_by_day_for_update(
        db,
        appointment.user_id,
        data.date
    )
    appointments = [
        appt for appt in appointments
        if appt.id != appointment.id
    ]

    if not is_time_available(data.date, new_start, new_end, appointments):
        raise HTTPException(409, "Horario no disponible")

    old_values = appointment_snapshot(appointment)
    appointment.date = data.date
    appointment.start_time = new_start
    appointment.end_time = new_end

    try:
        appointment = update_appointment(db, appointment)
    except IntegrityError:
        raise HTTPException(409, "Horario no disponible")

    record_appointment_history(
        db,
        appointment=appointment,
        action="rescheduled",
        changed_by_user_id=current_user.id,
        old_values=old_values,
        new_values=appointment_snapshot(appointment),
        reason=reason,
    )
    notify_appointment_event(db, appointment, "appointment_rescheduled")
    return appointment


def change_appointment_status(
    db: Session,
    appointment_id: int,
    new_status: AppointmentStatus,
    current_user: User,
) -> Appointment:
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_appointment(current_user, appointment)

    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso para cambiar el estado de la cita")

    if appointment.status in FINAL_STATES:
        raise HTTPException(400, "No se puede modificar una cita cerrada")

    if new_status.value == "cancelada":
        return cancel_appointment(db, appointment_id, current_user)

    allowed_statuses = {"confirmada", "completada", "no_show"}
    if new_status.value not in allowed_statuses:
        raise HTTPException(400, "Estado invalido")

    old_values = appointment_snapshot(appointment)
    appointment.status = new_status.value
    appointment = update_appointment(db, appointment)
    record_appointment_history(
        db,
        appointment=appointment,
        action=STATUS_ACTIONS[new_status.value],
        changed_by_user_id=current_user.id,
        old_values=old_values,
        new_values=appointment_snapshot(appointment),
    )
    event_by_status = {
        "confirmada": "appointment_confirmed",
        "completada": "appointment_completed",
    }
    if new_status.value in event_by_status:
        notify_appointment_event(db, appointment, event_by_status[new_status.value])
    if new_status.value == "no_show":
        register_no_show_penalty(db, appointment, current_user)
    return appointment


def list_appointment_history(
    db: Session,
    appointment_id: int,
    current_user: User,
) -> list[AppointmentHistory]:
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_appointment(current_user, appointment)
    return get_history_by_appointment(db, appointment_id)

def get_available_slots(
    db: Session,
    *,
    barber_id: int,
    service_id: int,
    appointment_date: date,
    branch_id: int | None = None,
    interval_minutes: int = 30
) -> list[time]:

    service = get_service_by_id(db, service_id)
    if not service or not service.is_active:
        raise HTTPException(404, "Servicio no encontrado")

    barber = get_user_by_id(db, barber_id)
    if not barber or not barber.is_active or barber.role != "barber":
        raise HTTPException(404, "Barbero no encontrado")

    if branch_id is not None:
        get_active_branch_or_404(db, branch_id)
        if barber.branch_id is not None and barber.branch_id != branch_id:
            raise HTTPException(400, "El barbero no pertenece a la sucursal seleccionada")
        if service.branch_id is not None and service.branch_id != branch_id:
            raise HTTPException(400, "El servicio no pertenece a la sucursal seleccionada")

    appointments = get_appointments_by_day(
        db,
        barber_id,
        appointment_date
    )

    slots = []
    schedules = get_active_schedules_for_day(
        db,
        barber_id,
        appointment_date.weekday()
    )

    for schedule in schedules:
        current_time = schedule.start_time

        while True:
            start_dt = datetime.combine(appointment_date, current_time)
            end_dt = start_dt + timedelta(minutes=service.duration_minutes)

            if end_dt.time() > schedule.end_time:
                break

            candidate_start = start_dt.time()
            candidate_end = end_dt.time()

            if (
                not is_inside_schedule_break(schedule, candidate_start, candidate_end)
                and not appointment_is_blocked(
                    db,
                    barber_id=barber_id,
                    appointment_date=appointment_date,
                    start_time=candidate_start,
                    end_time=candidate_end,
                )
                and is_time_available(
                    appointment_date,
                    candidate_start,
                    candidate_end,
                    appointments
                )
            ):
                slots.append(candidate_start)

            current_time = (
                start_dt + timedelta(minutes=interval_minutes)
            ).time()

    return slots


def update_appointment_status(
    db: Session,
    appointment_id: int,
    new_status: AppointmentStatus,
    current_user: User
):
    return change_appointment_status(db, appointment_id, new_status, current_user)

def auto_mark_no_show(db: Session):
    now = datetime.now()

    appointments = (
        db.query(Appointment)
        .filter(Appointment.status.in_(["agendada", "confirmada"]))
        .all()
    )

    for appointment in appointments:
        appointment_datetime = datetime.combine(
            appointment.date,
            appointment.start_time
        )

        if now > appointment_datetime + timedelta(minutes=NO_SHOW_TOLERANCE_MINUTES):
            appointment.status = "no_show"

    db.commit()
