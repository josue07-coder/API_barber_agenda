from datetime import date, time

from app.api.deps import get_current_user
from app.main import app
from app.models.appointment import Appointment
from app.models.client import Client
from app.models.service import Service
from app.models.user import User


def test_invalid_role_is_rejected(client, db):
    user = User(
        name="Target",
        email="target@test.com",
        password="x",
        role="barber",
        is_active=True,
    )
    db.add(user)
    db.commit()

    response = client.put(
        f"/api/v1/users/{user.id}",
        json={"role": "superadmin"},
    )

    assert response.status_code == 422


def test_invalid_appointment_status_is_rejected(client, db):
    barber = User(
        name="Barber",
        email="status-barber@test.com",
        password="x",
        role="barber",
        is_active=True,
    )
    client_model = Client(name="Client", phone="1234567", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, client_model, service])
    db.commit()

    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status="agendada",
    )
    db.add(appointment)
    db.commit()

    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/status",
        json={"status": "done"},
    )

    assert response.status_code == 422


def test_cors_allows_configured_origin(client):
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_private_route_without_token_returns_401(client_without_auth_override):
    response = client_without_auth_override.get("/api/v1/users/me")

    assert response.status_code == 401


def test_admin_route_with_wrong_role_returns_403(client):
    def override_barber_user():
        return User(
            id=10,
            name="Barber",
            email="barber-role@test.com",
            role="barber",
            is_active=True,
        )

    app.dependency_overrides[get_current_user] = override_barber_user

    response = client.get("/api/v1/users/")

    assert response.status_code == 403


def test_admin_route_with_correct_role_returns_200(client):
    response = client.get("/api/v1/users/")

    assert response.status_code == 200
