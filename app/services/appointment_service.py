from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timedelta, time, date
from typing import List, Optional

from app.schema.appointment import AppointmentCreate
from app.models.user import User
from app.models.appointment_status import AppointmentStatus
from app.models.appointment import Appointment
from app.repositories.appointment_repo import (
    get_appointments_by_day,
    get_appointments_by_barber,
    get_appointments_by_client,
    get_appointment_by_id,
    create_appointment,
    get_appointments,
    update_appointment,
)
from app.core.config import (
    BUSINESS_OPEN_TIME,
    BUSINESS_CLOSE_TIME,
    APPOINTMENT_BUFFER_MINUTES,
    NO_SHOW_TOLERANCE_MINUTES
)
from app.repositories.service_repo import get_service_by_id
from app.repositories.user_repo import get_user_by_id
from app.repositories.client_repo import get_client_by_id
from app.utils.time_utils import calculate_end_time


FINAL_STATES = {"completada", "cancelada", "no_show"}


def ensure_can_access_appointment(user: User, appointment: Appointment) -> None:
    if user.role == "admin":
        return

    if user.role == "barber" and appointment.user_id == user.id:
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


def create_new_appointment(
    db: Session,
    data: AppointmentCreate,
    current_user: User
) -> Appointment:

    barber = get_user_by_id(db, data.barber_id)
    if not barber or barber.role != "barber":
        raise HTTPException(400, "El usuario seleccionado no es un barbero")

    if current_user.role == "barber" and data.barber_id != current_user.id:
        raise HTTPException(403, "No puedes crear citas para otro barbero")

    client = get_client_by_id(db, data.client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    service = get_service_by_id(db, data.service_id)
    if not service:
        raise HTTPException(404, "Servicio no encontrado")
    
    client_appointments = get_appointments_by_client(db, data.client_id)

    for appt in client_appointments:
        if (
        appt.date == data.date and
        appt.service_id == data.service_id and
        appt.status not in {"cancelada", "no_show"}
    ):
            raise HTTPException(
                status_code=400,
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

    if start_time < BUSINESS_OPEN_TIME:
        raise HTTPException(400, "fuera del horario laboral")

    if end_time > BUSINESS_CLOSE_TIME:
        raise HTTPException(400, "la cita termina fuera del horario laboral")

    appointments = get_appointments_by_day(
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
        raise HTTPException(400, "Horario no disponible")

    appointment = Appointment(
        user_id=data.barber_id,
        client_id=data.client_id,
        service_id=data.service_id,
        date=data.date,
        start_time=start_time,
        end_time=end_time,
        status="agendada"
    )

    return create_appointment(db, appointment)


def list_all_appointments(
    db: Session,
    current_user: User,
    barber_id: Optional[int] = None,
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
        client_id=client_id,
        appointment_date=appointment_date,
        status=status,
        skip=skip,
        limit=limit
    )


from datetime import datetime

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
        new_date = data.get("date", appointment.date)

        new_start = data.get(
            "start_time",
            appointment.start_time
        ).replace(tzinfo=None)

        new_end = calculate_end_time(
            new_start,
            service.duration_minutes
        )

        if new_start < BUSINESS_OPEN_TIME:
            raise HTTPException(400, "Fuera del horario laboral")

        if new_end > BUSINESS_CLOSE_TIME:
            raise HTTPException(
                400,
                "La cita termina fuera del horario laboral"
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
            raise HTTPException(400, "Horario no disponible")

        appointment.date = new_date
        appointment.start_time = new_start
        appointment.end_time = new_end

    if "status" in data:
        if not isinstance(data["status"], AppointmentStatus):
            raise HTTPException(400, "Estado inválido")

        appointment.status = data["status"].value

    return update_appointment(db, appointment)



def list_appointments_by_barber(db: Session, barber_id: int):
    return get_appointments_by_barber(db, barber_id)


def list_appointments_by_client(db: Session, client_id: int):
    return get_appointments_by_client(db, client_id)


def list_appointments_by_day(db: Session, barber_id: int, appointment_date: date):
    return get_appointments_by_day(db, barber_id, appointment_date)


def cancel_appointment(
    db: Session,
    appointment_id: int,
    current_user: User
):
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_appointment(current_user, appointment)

    if appointment.status in FINAL_STATES:
        raise HTTPException(400, "La cita ya está cerrada")

    appointment_datetime = datetime.combine(
        appointment.date,
        appointment.start_time
    )

    now = datetime.now()

    if appointment_datetime - now < timedelta(minutes=30):
        raise HTTPException(
            status_code=400,
            detail="No se puede cancelar la cita con menos de 30 minutos de anticipación"
        )

    appointment.status = "cancelada"
    return update_appointment(db, appointment)

def get_available_slots(
    db: Session,
    *,
    barber_id: int,
    service_id: int,
    appointment_date: date,
    start_hour: int = 9,
    end_hour: int = 18,
    interval_minutes: int = 30
) -> list[time]:

    service = get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(404, "Servicio no encontrado")

    appointments = get_appointments_by_day(
        db,
        barber_id,
        appointment_date
    )

    slots = []
    current_time = time(start_hour, 0)

    while True:
        start_dt = datetime.combine(appointment_date, current_time)
        end_dt = start_dt + timedelta(minutes=service.duration_minutes)

        if end_dt.time() > time(end_hour, 0):
            break

        if is_time_available(
            appointment_date,
            start_dt.time(),
            end_dt.time(),
            appointments
        ):
            slots.append(current_time)

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
    appointment = get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(404, "Cita no encontrada")

    ensure_can_access_appointment(current_user, appointment)

    if appointment.status in FINAL_STATES:
        raise HTTPException(400, "No se puede modificar una cita cerrada")

    appointment.status = new_status.value
    return update_appointment(db, appointment)

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
