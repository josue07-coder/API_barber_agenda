from datetime import date, timedelta, time
from itertools import count


PHONE_COUNTER = count(1234567)


def future_date():
    return date.today() + timedelta(days=2)


def make_user(db, *, role="barber", email="barber-mgmt@test.com"):
    from app.models.user import User

    user = User(
        name=email.split("@")[0],
        email=email,
        password="x",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def make_client_service(db):
    from app.models.client import Client
    from app.models.service import Service

    client = Client(name="Cliente", phone=str(next(PHONE_COUNTER)), is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([client, service])
    db.commit()
    return client, service


def add_schedule(db, barber, schedule_date=None):
    from app.models.barber_schedule import BarberSchedule

    target_date = schedule_date or future_date()
    schedule = BarberSchedule(
        barber_id=barber.id,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(17, 0),
        break_start_time=time(12, 0),
        break_end_time=time(13, 0),
        is_active=True,
    )
    db.add(schedule)
    db.commit()
    return schedule


def create_valid_appointment(db, barber, client_model=None, service=None, appointment_date=None, start_time=None):
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment

    appointment_date = appointment_date or future_date()
    start_time = start_time or time(10, 0)
    if client_model is None or service is None:
        client_model, service = make_client_service(db)
    add_schedule(db, barber, appointment_date)
    return create_new_appointment(
        db,
        AppointmentCreate(
            barber_id=barber.id,
            client_id=client_model.id,
            service_id=service.id,
            date=appointment_date,
            start_time=start_time,
        ),
        barber,
    )


def test_cancel_valid_appointment(client, db):
    barber = make_user(db, email="cancel-valid@test.com")
    appointment = create_valid_appointment(db, barber)

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/cancel",
        json={"reason": "Cliente no puede asistir"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelada"
    assert data["cancellation_reason"] == "Cliente no puede asistir"
    assert data["cancelled_at"] is not None


def test_cancel_completed_appointment_rejected(client, db):
    barber = make_user(db, email="cancel-completed@test.com")
    appointment = create_valid_appointment(db, barber)
    appointment.status = "completada"
    db.commit()

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 400


def test_cancel_already_cancelled_appointment_rejected(client, db):
    barber = make_user(db, email="cancel-twice@test.com")
    appointment = create_valid_appointment(db, barber)

    first_response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")
    second_response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert first_response.status_code == 200
    assert second_response.status_code == 400


def test_barber_cannot_cancel_other_barber_appointment(client, db):
    from app.api.deps import get_current_user
    from app.main import app

    owner = make_user(db, email="owner-cancel@test.com")
    other = make_user(db, email="other-cancel@test.com")
    appointment = create_valid_appointment(db, owner)

    def override_other_barber():
        return other

    app.dependency_overrides[get_current_user] = override_other_barber

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 403


def test_reschedule_valid_appointment(client, db):
    barber = make_user(db, email="reschedule-valid@test.com")
    appointment_date = future_date()
    appointment = create_valid_appointment(db, barber, appointment_date=appointment_date, start_time=time(10, 0))

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/reschedule",
        json={
            "date": appointment_date.isoformat(),
            "start_time": "14:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["start_time"] == "14:00:00"


def test_reschedule_to_occupied_time_rejected(client, db):
    barber = make_user(db, email="reschedule-occupied@test.com")
    appointment_date = future_date()
    client_one, service = make_client_service(db)
    client_two, _ = make_client_service(db)
    appointment = create_valid_appointment(
        db, barber, client_one, service, appointment_date=appointment_date, start_time=time(10, 0)
    )
    create_valid_appointment(
        db, barber, client_two, service, appointment_date=appointment_date, start_time=time(11, 0)
    )

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/reschedule",
        json={
            "date": appointment_date.isoformat(),
            "start_time": "11:00:00",
        },
    )

    assert response.status_code == 409


def test_reschedule_to_blocked_time_rejected(client, db):
    from app.models.barber_time_block import BarberTimeBlock

    barber = make_user(db, email="reschedule-blocked@test.com")
    appointment_date = future_date()
    appointment = create_valid_appointment(db, barber, appointment_date=appointment_date, start_time=time(10, 0))
    db.add(
        BarberTimeBlock(
            barber_id=barber.id,
            date=appointment_date,
            start_time=time(14, 0),
            end_time=time(15, 0),
            is_full_day=False,
            is_active=True,
        )
    )
    db.commit()

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/reschedule",
        json={
            "date": appointment_date.isoformat(),
            "start_time": "14:00:00",
        },
    )

    assert response.status_code == 409


def test_reschedule_outside_schedule_rejected(client, db):
    barber = make_user(db, email="reschedule-outside@test.com")
    appointment_date = future_date()
    appointment = create_valid_appointment(db, barber, appointment_date=appointment_date, start_time=time(10, 0))

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/reschedule",
        json={
            "date": appointment_date.isoformat(),
            "start_time": "18:00:00",
        },
    )

    assert response.status_code == 400


def test_confirm_complete_and_no_show_appointments(client, db):
    barber = make_user(db, email="status-flow@test.com")
    appointment_date = future_date()

    confirmed = create_valid_appointment(db, barber, appointment_date=appointment_date, start_time=time(9, 0))
    completed = create_valid_appointment(db, barber, appointment_date=appointment_date, start_time=time(10, 0))
    no_show = create_valid_appointment(db, barber, appointment_date=appointment_date, start_time=time(11, 0))

    assert client.patch(f"/api/v1/appointments/{confirmed.id}/confirm").json()["status"] == "confirmada"
    assert client.patch(f"/api/v1/appointments/{completed.id}/complete").json()["status"] == "completada"
    assert client.patch(f"/api/v1/appointments/{no_show.id}/no-show").json()["status"] == "no_show"


def test_history_records_created_cancelled_rescheduled_and_status_changes(client, db):
    barber = make_user(db, email="history@test.com")
    appointment_date = future_date()
    appointment = create_valid_appointment(db, barber, appointment_date=appointment_date, start_time=time(10, 0))

    client.patch(
        f"/api/v1/appointments/{appointment.id}/reschedule",
        json={
            "date": appointment_date.isoformat(),
            "start_time": "14:00:00",
        },
    )
    client.patch(f"/api/v1/appointments/{appointment.id}/confirm")
    client.patch(
        f"/api/v1/appointments/{appointment.id}/cancel",
        json={"reason": "Cambio de planes"},
    )

    response = client.get(f"/api/v1/appointments/{appointment.id}/history")

    assert response.status_code == 200
    actions = [item["action"] for item in response.json()]
    assert "created" in actions
    assert "rescheduled" in actions
    assert "confirmed" in actions
    assert "cancelled" in actions


def test_user_without_permission_receives_403(client, db):
    from app.api.deps import get_current_user
    from app.main import app

    barber = make_user(db, email="permission-owner@test.com")
    client_user = make_user(db, role="client", email="permission-client@test.com")
    appointment = create_valid_appointment(db, barber)

    def override_client_user():
        return client_user

    app.dependency_overrides[get_current_user] = override_client_user

    response = client.patch(f"/api/v1/appointments/{appointment.id}/confirm")

    assert response.status_code == 403
