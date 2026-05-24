import pytest
from fastapi import HTTPException
from datetime import date, timedelta


def future_date():
    return date.today() + timedelta(days=1)


def add_schedule(db, barber, schedule_date=None, start=None, end=None, break_start=None, break_end=None):
    from datetime import time
    from app.models.barber_schedule import BarberSchedule

    target_date = schedule_date or future_date()
    schedule = BarberSchedule(
        barber_id=barber.id,
        weekday=target_date.weekday(),
        start_time=start or time(9, 0),
        end_time=end or time(18, 0),
        break_start_time=break_start,
        break_end_time=break_end,
        is_active=True,
    )
    db.add(schedule)
    db.commit()
    return schedule


def test_create_appointment_success(db):
    from app.services.appointment_service import create_new_appointment
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.schema.appointment import AppointmentCreate
    from datetime import time

    from app.core.security import get_password_hash

    barber = User(name="Barber", email="b@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    client = Client(name="Juan", phone="1234567", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)

    db.add_all([barber, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0)
    )

    appointment = create_new_appointment(db, data, barber)

    assert appointment.id is not None
    assert appointment.status == "agendada"


def test_appointment_time_conflict(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(
        name="Barber",
        email="b@b.com",
        password=get_password_hash("test1234"),
        role="barber",
        is_active=True
    )

    client = Client(name="Juan", phone="1234567", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)

    db.add_all([barber, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0)
    )

    create_new_appointment(db, data, barber)

    with pytest.raises(HTTPException):
        create_new_appointment(db, data, barber)


def test_appointment_before_opening_hours(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(
        name="Barber",
        email="b2@b.com",
        password=get_password_hash("test1234"),
        role="barber",
        is_active=True
    )
    client = Client(name="Pedro", phone="2222222", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)

    db.add_all([barber, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(8, 0)
    )

    with pytest.raises(HTTPException):
        create_new_appointment(db, data, barber)


def test_appointment_after_closing_hours(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(
        name="Barber",
        email="b3@b.com",
        password=get_password_hash("test1234"),
        role="barber",
        is_active=True
    )
    client = Client(name="Luis", phone="3333333", is_active=True)
    service = Service(
        name="Servicio largo",
        duration_minutes=60,
        price=20,
        is_active=True
    )

    db.add_all([barber, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(17, 30)
    )

    with pytest.raises(HTTPException):
        create_new_appointment(db, data, barber)


def test_appointment_buffer_conflict(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(
        name="Barber",
        email="b4@b.com",
        password=get_password_hash("test1234"),
        role="barber",
        is_active=True
    )
    client1 = Client(name="Ana", phone="4444444", is_active=True)
    client2 = Client(name="Maria", phone="5555555", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)

    db.add_all([barber, client1, client2, service])
    db.commit()
    add_schedule(db, barber)

    first = AppointmentCreate(
        barber_id=barber.id,
        client_id=client1.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0)
    )

    second = AppointmentCreate(
        barber_id=barber.id,
        client_id=client2.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 30)
    )

    create_new_appointment(db, first, barber)

    with pytest.raises(HTTPException):
        create_new_appointment(db, second, barber)


def test_appointment_valid_with_buffer(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(
        name="Barber",
        email="b5@b.com",
        password=get_password_hash("test1234"),
        role="barber",
        is_active=True
    )
    client1 = Client(name="Carlos", phone="6666666", is_active=True)
    client2 = Client(name="Rosa", phone="7777777", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)

    db.add_all([barber, client1, client2, service])
    db.commit()
    add_schedule(db, barber)

    first = AppointmentCreate(
        barber_id=barber.id,
        client_id=client1.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0)
    )

    second = AppointmentCreate(
        barber_id=barber.id,
        client_id=client2.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 40)
    )

    create_new_appointment(db, first, barber)
    appt = create_new_appointment(db, second, barber)

    assert appt is not None


def test_cannot_change_completed_appointment(db):
    from app.services.appointment_service import update_appointment_status
    from app.models.appointment import Appointment
    from app.models.user import User
    from datetime import date, time

    user = User(
        name="Admin",
        email="admin@test.com",
        password="x",
        role="admin",
        is_active=True
    )
    appointment = Appointment(
        user_id=1,
        client_id=1,
        service_id=1,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status="completada"
    )

    db.add_all([user, appointment])
    db.commit()

    with pytest.raises(HTTPException):
        update_appointment_status(
            db,
            appointment.id,
            "cancelada",
            user
        )


def test_create_appointment_in_past_returns_400(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(name="Barber", email="past@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    client = Client(name="Past Client", phone="1111111", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=date.today() - timedelta(days=1),
        start_time=time(10, 0),
    )

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(db, data, barber)

    assert exc.value.status_code == 400


def test_create_overlapping_appointment_returns_409(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(name="Barber", email="overlap@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    client1 = Client(name="Client One", phone="1212121", is_active=True)
    client2 = Client(name="Client Two", phone="2323232", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, client1, client2, service])
    db.commit()
    add_schedule(db, barber)

    first = AppointmentCreate(
        barber_id=barber.id,
        client_id=client1.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0),
    )
    second = AppointmentCreate(
        barber_id=barber.id,
        client_id=client2.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 15),
    )

    create_new_appointment(db, first, barber)

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(db, second, barber)

    assert exc.value.status_code == 409


def test_create_same_start_time_returns_409(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(name="Barber", email="same-time@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    client1 = Client(name="Client One", phone="3434343", is_active=True)
    client2 = Client(name="Client Two", phone="4545454", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, client1, client2, service])
    db.commit()
    add_schedule(db, barber)

    first = AppointmentCreate(
        barber_id=barber.id,
        client_id=client1.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(11, 0),
    )
    second = AppointmentCreate(
        barber_id=barber.id,
        client_id=client2.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(11, 0),
    )

    create_new_appointment(db, first, barber)

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(db, second, barber)

    assert exc.value.status_code == 409


def test_create_appointment_with_inactive_client_returns_404(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(name="Barber", email="inactive-client@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    client = Client(name="Inactive Client", phone="5656565", is_active=False)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0),
    )

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(db, data, barber)

    assert exc.value.status_code == 404


def test_create_appointment_with_inactive_service_returns_404(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(name="Barber", email="inactive-service@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    client = Client(name="Client", phone="6767676", is_active=True)
    service = Service(name="Inactive Service", duration_minutes=30, price=10, is_active=False)
    db.add_all([barber, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0),
    )

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(db, data, barber)

    assert exc.value.status_code == 404


def test_create_appointment_with_inactive_barber_returns_404(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(name="Barber", email="inactive-barber@b.com", password=get_password_hash("test1234"), role="barber", is_active=False)
    admin = User(name="Admin", email="admin-inactive-barber@test.com", password=get_password_hash("test1234"), role="admin", is_active=True)
    client = Client(name="Client", phone="7878787", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, admin, client, service])
    db.commit()

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0),
    )

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(db, data, admin)

    assert exc.value.status_code == 404


def test_create_appointment_without_permission_returns_403(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import time

    barber = User(name="Barber", email="permission-barber@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    other_user = User(name="Client User", email="client-user@test.com", password=get_password_hash("test1234"), role="client", is_active=True)
    client = Client(name="Client", phone="8989898", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, other_user, client, service])
    db.commit()
    add_schedule(db, barber)

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=future_date(),
        start_time=time(10, 0),
    )

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(db, data, other_user)

    assert exc.value.status_code == 403
