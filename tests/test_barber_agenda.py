from datetime import date, timedelta, time


def next_weekday(weekday: int) -> date:
    today = date.today()
    delta = (weekday - today.weekday()) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


def make_user(db, *, role="barber", email="barber-agenda@test.com", is_active=True):
    from app.models.user import User

    user = User(
        name=email.split("@")[0],
        email=email,
        password="x",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    return user


def make_client_and_service(db):
    from app.models.client import Client
    from app.models.service import Service

    client = Client(name="Cliente", phone="1234567", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([client, service])
    db.commit()
    return client, service


def create_schedule_payload(barber_id, weekday=0, start="09:00:00", end="17:00:00", **extra):
    payload = {
        "barber_id": barber_id,
        "weekday": weekday,
        "start_time": start,
        "end_time": end,
        "is_active": True,
    }
    payload.update(extra)
    return payload


def test_create_valid_schedule(client, db):
    barber = make_user(db, email="schedule-valid@test.com")

    response = client.post(
        "/api/v1/barber-schedules/",
        json=create_schedule_payload(barber.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["barber_id"] == barber.id
    assert data["weekday"] == 0


def test_invalid_schedule_hours_returns_422(client, db):
    barber = make_user(db, email="schedule-invalid@test.com")

    response = client.post(
        "/api/v1/barber-schedules/",
        json=create_schedule_payload(barber.id, start="17:00:00", end="09:00:00"),
    )

    assert response.status_code == 422


def test_overlapping_schedule_returns_409(client, db):
    barber = make_user(db, email="schedule-overlap@test.com")

    response = client.post(
        "/api/v1/barber-schedules/",
        json=create_schedule_payload(barber.id, start="09:00:00", end="13:00:00"),
    )
    assert response.status_code == 200

    response = client.post(
        "/api/v1/barber-schedules/",
        json=create_schedule_payload(barber.id, start="12:00:00", end="16:00:00"),
    )

    assert response.status_code == 409


def test_barber_cannot_manage_other_barber_schedule(client, db):
    from app.api.deps import get_current_user
    from app.main import app

    barber = make_user(db, email="owner@test.com")
    other_barber = make_user(db, email="other@test.com")

    def override_barber():
        return barber

    app.dependency_overrides[get_current_user] = override_barber

    response = client.post(
        "/api/v1/barber-schedules/",
        json=create_schedule_payload(other_barber.id),
    )

    assert response.status_code == 403


def test_admin_can_manage_other_barber_schedule(client, db):
    barber = make_user(db, email="admin-target@test.com")

    response = client.post(
        "/api/v1/barber-schedules/",
        json=create_schedule_payload(barber.id),
    )

    assert response.status_code == 200


def test_create_full_day_block(client, db):
    barber = make_user(db, email="full-block@test.com")
    block_date = next_weekday(1)

    response = client.post(
        "/api/v1/barber-time-blocks/",
        json={
            "barber_id": barber.id,
            "date": block_date.isoformat(),
            "is_full_day": True,
            "reason": "Vacaciones",
        },
    )

    assert response.status_code == 200
    assert response.json()["is_full_day"] is True


def test_create_partial_block(client, db):
    barber = make_user(db, email="partial-block@test.com")
    block_date = next_weekday(1)

    response = client.post(
        "/api/v1/barber-time-blocks/",
        json={
            "barber_id": barber.id,
            "date": block_date.isoformat(),
            "start_time": "11:00:00",
            "end_time": "12:00:00",
            "is_full_day": False,
            "reason": "Diligencia",
        },
    )

    assert response.status_code == 200
    assert response.json()["start_time"] == "11:00:00"


def test_appointment_inside_block_is_rejected(db):
    from app.models.barber_schedule import BarberSchedule
    from app.models.barber_time_block import BarberTimeBlock
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment
    from fastapi import HTTPException
    import pytest

    barber = make_user(db, email="blocked-appointment@test.com")
    appt_date = next_weekday(2)
    client_model, service = make_client_and_service(db)
    db.add_all([
        BarberSchedule(
            barber_id=barber.id,
            weekday=appt_date.weekday(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        ),
        BarberTimeBlock(
            barber_id=barber.id,
            date=appt_date,
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_full_day=False,
            is_active=True,
        ),
    ])
    db.commit()

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(
            db,
            AppointmentCreate(
                barber_id=barber.id,
                client_id=client_model.id,
                service_id=service.id,
                date=appt_date,
                start_time=time(10, 30),
            ),
            barber,
        )

    assert exc.value.status_code == 409


def test_appointment_outside_schedule_is_rejected(db):
    from app.models.barber_schedule import BarberSchedule
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment
    from fastapi import HTTPException
    import pytest

    barber = make_user(db, email="outside-schedule@test.com")
    appt_date = next_weekday(3)
    client_model, service = make_client_and_service(db)
    db.add(
        BarberSchedule(
            barber_id=barber.id,
            weekday=appt_date.weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            is_active=True,
        )
    )
    db.commit()

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(
            db,
            AppointmentCreate(
                barber_id=barber.id,
                client_id=client_model.id,
                service_id=service.id,
                date=appt_date,
                start_time=time(13, 0),
            ),
            barber,
        )

    assert exc.value.status_code == 400


def test_appointment_during_break_is_rejected(db):
    from app.models.barber_schedule import BarberSchedule
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment
    from fastapi import HTTPException
    import pytest

    barber = make_user(db, email="break-schedule@test.com")
    appt_date = next_weekday(4)
    client_model, service = make_client_and_service(db)
    db.add(
        BarberSchedule(
            barber_id=barber.id,
            weekday=appt_date.weekday(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            break_start_time=time(12, 0),
            break_end_time=time(13, 0),
            is_active=True,
        )
    )
    db.commit()

    with pytest.raises(HTTPException) as exc:
        create_new_appointment(
            db,
            AppointmentCreate(
                barber_id=barber.id,
                client_id=client_model.id,
                service_id=service.id,
                date=appt_date,
                start_time=time(12, 15),
            ),
            barber,
        )

    assert exc.value.status_code == 400


def test_available_slots_respect_schedule_breaks_blocks_and_appointments(db):
    from app.models.appointment import Appointment
    from app.models.barber_schedule import BarberSchedule
    from app.models.barber_time_block import BarberTimeBlock
    from app.services.appointment_service import get_available_slots

    barber = make_user(db, email="slots@test.com")
    slot_date = next_weekday(5)
    client_model, service = make_client_and_service(db)
    db.add_all([
        BarberSchedule(
            barber_id=barber.id,
            weekday=slot_date.weekday(),
            start_time=time(9, 0),
            end_time=time(12, 0),
            break_start_time=time(10, 0),
            break_end_time=time(10, 30),
            is_active=True,
        ),
        BarberTimeBlock(
            barber_id=barber.id,
            date=slot_date,
            start_time=time(11, 0),
            end_time=time(11, 30),
            is_full_day=False,
            is_active=True,
        ),
        Appointment(
            user_id=barber.id,
            client_id=client_model.id,
            service_id=service.id,
            date=slot_date,
            start_time=time(9, 0),
            end_time=time(9, 30),
            status="agendada",
        ),
    ])
    db.commit()

    slots = get_available_slots(
        db,
        barber_id=barber.id,
        service_id=service.id,
        appointment_date=slot_date,
    )

    assert time(9, 0) not in slots
    assert time(10, 0) not in slots
    assert time(11, 0) not in slots
    assert time(10, 30) in slots
    assert time(11, 30) in slots
