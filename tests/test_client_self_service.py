from datetime import date, timedelta, time

from app.api.deps import get_current_user
from app.main import app


def future_date():
    return date.today() + timedelta(days=4)


def make_barber(db, email="self-barber@test.com"):
    from app.models.user import User

    barber = User(
        name="Self Barber",
        email=email,
        password="x",
        role="barber",
        is_active=True,
    )
    db.add(barber)
    db.commit()
    return barber


def make_client_user(db, email="self-client@test.com", phone="8092223333"):
    from app.models.client import Client
    from app.models.user import User

    client_model = Client(name="Self Client", phone=phone, is_active=True)
    db.add(client_model)
    db.commit()
    user = User(
        name="Self Client",
        email=email,
        password="x",
        role="client",
        client_id=client_model.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, client_model


def make_service_and_schedule(db, barber, target_date):
    from app.models.barber_schedule import BarberSchedule
    from app.models.service import Service

    service = Service(name="Self Corte", duration_minutes=30, price=100, is_active=True)
    schedule = BarberSchedule(
        barber_id=barber.id,
        weekday=target_date.weekday(),
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_active=True,
    )
    db.add_all([service, schedule])
    db.commit()
    return service


def create_appointment_for_client(db, barber, client_user, client_model, *, start_time=time(10, 0)):
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment

    target_date = future_date()
    service = make_service_and_schedule(db, barber, target_date)
    appointment = create_new_appointment(
        db,
        AppointmentCreate(
            barber_id=barber.id,
            client_id=client_model.id,
            service_id=service.id,
            date=target_date,
            start_time=start_time,
        ),
        client_user,
    )
    return appointment, service


def override_user(user):
    def _override():
        return user

    return _override


def test_register_client(client_without_auth_override):
    response = client_without_auth_override.post(
        "/api/v1/auth/register-client",
        json={
            "name": "Cliente Portal",
            "email": "portal-client@test.com",
            "password": "Client12345",
            "phone": "8095557777",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_client_authenticated_sees_own_appointments(client, db):
    barber = make_barber(db, "self-appt-barber@test.com")
    client_user, client_model = make_client_user(db, "self-appt@test.com", "8091000001")
    appointment, _ = create_appointment_for_client(db, barber, client_user, client_model)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.get("/api/v1/me/appointments")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [appointment.id]


def test_client_does_not_see_other_client_appointments(client, db):
    barber = make_barber(db, "self-other-barber@test.com")
    owner_user, owner_client = make_client_user(db, "owner@test.com", "8091000002")
    other_user, _ = make_client_user(db, "other@test.com", "8091000003")
    create_appointment_for_client(db, barber, owner_user, owner_client)
    app.dependency_overrides[get_current_user] = override_user(other_user)

    response = client.get("/api/v1/me/appointments")

    assert response.status_code == 200
    assert response.json() == []


def test_client_creates_own_appointment(client, db):
    barber = make_barber(db, "self-create-barber@test.com")
    client_user, client_model = make_client_user(db, "self-create@test.com", "8091000004")
    target_date = future_date()
    service = make_service_and_schedule(db, barber, target_date)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.post(
        "/api/v1/appointments/",
        json={
            "barber_id": barber.id,
            "client_id": client_model.id,
            "service_id": service.id,
            "date": target_date.isoformat(),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 200
    assert response.json()["client_id"] == client_model.id


def test_client_cannot_create_appointment_for_other_client(client, db):
    barber = make_barber(db, "self-create-other-barber@test.com")
    client_user, _ = make_client_user(db, "self-create-other@test.com", "8091000005")
    _, other_client = make_client_user(db, "self-target-other@test.com", "8091000006")
    target_date = future_date()
    service = make_service_and_schedule(db, barber, target_date)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.post(
        "/api/v1/appointments/",
        json={
            "barber_id": barber.id,
            "client_id": other_client.id,
            "service_id": service.id,
            "date": target_date.isoformat(),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 403


def test_client_cancels_own_appointment(client, db):
    barber = make_barber(db, "self-cancel-barber@test.com")
    client_user, client_model = make_client_user(db, "self-cancel@test.com", "8091000007")
    appointment, _ = create_appointment_for_client(db, barber, client_user, client_model)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelada"


def test_client_cannot_cancel_other_appointment(client, db):
    barber = make_barber(db, "self-no-cancel-barber@test.com")
    owner_user, owner_client = make_client_user(db, "self-owner@test.com", "8091000008")
    other_user, _ = make_client_user(db, "self-not-owner@test.com", "8091000009")
    appointment, _ = create_appointment_for_client(db, barber, owner_user, owner_client)
    app.dependency_overrides[get_current_user] = override_user(other_user)

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 403


def test_client_sees_own_payments_and_not_others(client, db):
    barber = make_barber(db, "self-payments-barber@test.com")
    client_user, client_model = make_client_user(db, "self-payments@test.com", "8091000010")
    other_user, other_client = make_client_user(db, "self-payments-other@test.com", "8091000011")
    appointment, _ = create_appointment_for_client(db, barber, client_user, client_model, start_time=time(10, 0))
    other_appointment, _ = create_appointment_for_client(db, barber, other_user, other_client, start_time=time(11, 0))

    payment = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": appointment.id,
            "amount": "25.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    ).json()
    other_payment = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": other_appointment.id,
            "amount": "30.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    ).json()
    app.dependency_overrides[get_current_user] = override_user(client_user)

    own = client.get("/api/v1/me/payments")
    other = client.get(f"/api/v1/payments/{other_payment['id']}")

    assert own.status_code == 200
    assert [item["id"] for item in own.json()] == [payment["id"]]
    assert other.status_code == 403


def test_client_sees_own_notifications(client, db):
    barber = make_barber(db, "self-notifications-barber@test.com")
    client_user, client_model = make_client_user(db, "self-notifications@test.com", "8091000012")
    create_appointment_for_client(db, barber, client_user, client_model)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.get("/api/v1/me/notifications")

    assert response.status_code == 200
    assert response.json()
    assert all(item["recipient_id"] == client_user.client_id for item in response.json())


def test_client_cannot_access_admin_reports(client, db):
    client_user, _ = make_client_user(db, "self-report@test.com", "8091000013")
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.get(
        f"/api/v1/reports/dashboard?start_date={future_date()}&end_date={future_date()}"
    )

    assert response.status_code == 403
