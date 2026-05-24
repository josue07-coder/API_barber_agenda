from datetime import datetime, timedelta, time

import pytest
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_user
from app.main import app


def make_barber(db, email="cutoff-barber@test.com"):
    from app.models.user import User

    barber = User(
        name="Cutoff Barber",
        email=email,
        password="x",
        role="barber",
        is_active=True,
    )
    db.add(barber)
    db.commit()
    return barber


def make_client_user(db, email, phone):
    from app.models.client import Client
    from app.models.user import User

    client_model = Client(name="Cutoff Client", phone=phone, is_active=True)
    db.add(client_model)
    db.commit()
    user = User(
        name="Cutoff Client",
        email=email,
        password="x",
        role="client",
        client_id=client_model.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user, client_model


def make_service_schedule(db, barber, target_date):
    from app.models.barber_schedule import BarberSchedule
    from app.models.service import Service

    service = Service(name="Cutoff Service", duration_minutes=30, price=100, is_active=True)
    schedule = BarberSchedule(
        barber_id=barber.id,
        weekday=target_date.weekday(),
        start_time=time(8, 0),
        end_time=time(20, 0),
        is_active=True,
    )
    db.add_all([service, schedule])
    db.commit()
    return service


def create_direct_appointment(db, barber, client_model, service, appointment_dt):
    from app.models.appointment import Appointment

    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        date=appointment_dt.date(),
        start_time=appointment_dt.time().replace(microsecond=0),
        end_time=(appointment_dt + timedelta(minutes=30)).time().replace(microsecond=0),
        status="agendada",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def override_user(user):
    def _override():
        return user

    return _override


def test_clients_phone_unique_constraint(db):
    from app.models.client import Client

    db.add(Client(name="Phone One", phone="8093330000", is_active=True))
    db.commit()
    db.add(Client(name="Phone Two", phone="8093330000", is_active=True))

    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()


def test_client_updates_own_profile(client, db):
    client_user, client_model = make_client_user(db, "profile@test.com", "8093330001")
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(
        "/api/v1/me/client-profile",
        json={
            "name": "Nuevo Nombre",
            "phone": "8093339999",
            "notes": "Nota cliente",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Nuevo Nombre"
    assert response.json()["phone"] == "8093339999"
    db.refresh(client_model)
    db.refresh(client_user)
    assert client_model.name == "Nuevo Nombre"
    assert client_user.name == "Nuevo Nombre"


def test_client_cannot_update_forbidden_profile_fields(client, db):
    client_user, _ = make_client_user(db, "profile-forbidden@test.com", "8093330002")
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(
        "/api/v1/me/client-profile",
        json={"client_id": 999, "role": "admin", "is_active": False},
    )

    assert response.status_code == 422


def test_client_cannot_update_profile_to_existing_phone(client, db):
    client_user, _ = make_client_user(db, "profile-owner@test.com", "8093330003")
    make_client_user(db, "profile-other@test.com", "8093330004")
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(
        "/api/v1/me/client-profile",
        json={"phone": "8093330004"},
    )

    assert response.status_code == 409


def test_client_cannot_cancel_inside_cutoff(client, db):
    barber = make_barber(db, "cutoff-cancel-barber@test.com")
    client_user, client_model = make_client_user(db, "cutoff-cancel@test.com", "8093330005")
    appt_dt = datetime.now() + timedelta(hours=23)
    service = make_service_schedule(db, barber, appt_dt.date())
    appointment = create_direct_appointment(db, barber, client_model, service, appt_dt)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 409


def test_client_can_cancel_outside_cutoff(client, db):
    barber = make_barber(db, "cutoff-cancel-ok-barber@test.com")
    client_user, client_model = make_client_user(db, "cutoff-cancel-ok@test.com", "8093330006")
    appt_dt = datetime.now() + timedelta(hours=49)
    service = make_service_schedule(db, barber, appt_dt.date())
    appointment = create_direct_appointment(db, barber, client_model, service, appt_dt)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 200


def test_client_cannot_reschedule_inside_cutoff(client, db):
    barber = make_barber(db, "cutoff-reschedule-barber@test.com")
    client_user, client_model = make_client_user(db, "cutoff-reschedule@test.com", "8093330007")
    appt_dt = datetime.now() + timedelta(hours=23)
    service = make_service_schedule(db, barber, appt_dt.date())
    appointment = create_direct_appointment(db, barber, client_model, service, appt_dt)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/reschedule",
        json={
            "date": appt_dt.date().isoformat(),
            "start_time": "15:00:00",
        },
    )

    assert response.status_code == 409


def test_client_can_reschedule_outside_cutoff(client, db):
    barber = make_barber(db, "cutoff-reschedule-ok-barber@test.com")
    client_user, client_model = make_client_user(db, "cutoff-reschedule-ok@test.com", "8093330008")
    appt_dt = datetime.now() + timedelta(hours=49)
    service = make_service_schedule(db, barber, appt_dt.date())
    appointment = create_direct_appointment(db, barber, client_model, service, appt_dt)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/reschedule",
        json={
            "date": appt_dt.date().isoformat(),
            "start_time": "15:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["start_time"] == "15:00:00"


def test_admin_is_not_limited_by_client_cutoff(client, db):
    barber = make_barber(db, "cutoff-admin-barber@test.com")
    _, client_model = make_client_user(db, "cutoff-admin-client@test.com", "8093330009")
    appt_dt = datetime.now() + timedelta(hours=2)
    service = make_service_schedule(db, barber, appt_dt.date())
    appointment = create_direct_appointment(db, barber, client_model, service, appt_dt)

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 200
