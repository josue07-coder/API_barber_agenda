import pytest
def test_create_appointment_success(db):
    from app.services.appointment_service import create_new_appointment
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.schema.appointment import AppointmentCreate
    from datetime import date, time

    from app.core.security import get_password_hash

    barber = User(name="Barber", email="b@b.com", password=get_password_hash("test1234"), role="barber", is_active=True)
    client = Client(name="Juan", phone="1234567", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)

    db.add_all([barber, client, service])
    db.commit()

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(10, 0)
    )

    appointment = create_new_appointment(db, data)

    assert appointment.id is not None
    assert appointment.status == "agendada"

def test_appointment_time_conflict(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import date, time

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

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(10, 0)
    )

    create_new_appointment(db, data)

    # Intentar crear otra cita en el mismo horario
    with pytest.raises(ValueError):
        create_new_appointment(db, data)

def test_appointment_before_opening_hours(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import date, time

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

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(8, 0)  #  antes de abrir
    )

    with pytest.raises(ValueError):
        create_new_appointment(db, data)

def test_appointment_after_closing_hours(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import date, time

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

    data = AppointmentCreate(
        barber_id=barber.id,
        client_id=client.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(17, 30)  #  termina después de las 18:00
    )

    with pytest.raises(ValueError):
        create_new_appointment(db, data)

def test_appointment_buffer_conflict(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import date, time

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

    first = AppointmentCreate(
        barber_id=barber.id,
        client_id=client1.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(10, 0)
    )

    second = AppointmentCreate(
        barber_id=barber.id,
        client_id=client2.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(10, 30)  #  no respeta buffer
    )

    create_new_appointment(db, first)

    with pytest.raises(ValueError):
        create_new_appointment(db, second)

def test_appointment_valid_with_buffer(db):
    from app.services.appointment_service import create_new_appointment
    from app.schema.appointment import AppointmentCreate
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.core.security import get_password_hash
    from datetime import date, time

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

    first = AppointmentCreate(
        barber_id=barber.id,
        client_id=client1.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(10, 0)
    )

    second = AppointmentCreate(
        barber_id=barber.id,
        client_id=client2.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(10, 40)  #  respeta buffer
    )

    create_new_appointment(db, first)
    appt = create_new_appointment(db, second)

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

    with pytest.raises(ValueError):
        update_appointment_status(
            db,
            appointment.id,
            "cancelada",
            user
        )

