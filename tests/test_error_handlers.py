from fastapi import APIRouter

from app.core.config import settings
from app.main import app


router = APIRouter()


@router.get("/__test__/unexpected-error")
def unexpected_error():
    raise RuntimeError("secret password token raw sql")


if not any(getattr(route, "path", None) == "/__test__/unexpected-error" for route in app.routes):
    app.include_router(router)


def assert_error_shape(data, error_code):
    assert data["success"] is False
    assert data["error_code"] == error_code
    assert isinstance(data["message"], str)
    assert "details" in data
    assert "request_id" in data


def test_404_uses_standard_error_format(client):
    response = client.get("/api/v1/users/999")

    assert response.status_code == 404
    data = response.json()
    assert_error_shape(data, "not_found")
    assert data["message"] == "Usuario no encontrado"
    assert response.headers["X-Request-ID"] == data["request_id"]


def test_422_uses_standard_error_format_with_details(client):
    response = client.put("/api/v1/users/1", json={"email": "not-an-email"})

    assert response.status_code == 422
    data = response.json()
    assert_error_shape(data, "validation_error")
    assert "errors" in data["details"]


def test_409_uses_standard_error_format(client, db):
    from app.models.client import Client
    from app.models.barber_schedule import BarberSchedule
    from app.models.service import Service
    from app.models.user import User
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment
    from datetime import date, timedelta, time

    barber = User(name="Barber", email="error-409@b.com", password="x", role="barber", is_active=True)
    client_one = Client(name="One", phone="1111111", is_active=True)
    client_two = Client(name="Two", phone="2222222", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=10, is_active=True)
    db.add_all([barber, client_one, client_two, service])
    db.commit()

    appointment_date = date.today() + timedelta(days=1)
    db.add(
        BarberSchedule(
            barber_id=barber.id,
            weekday=appointment_date.weekday(),
            start_time=time(9, 0),
            end_time=time(18, 0),
            is_active=True,
        )
    )
    db.commit()

    create_new_appointment(
        db,
        AppointmentCreate(
            barber_id=barber.id,
            client_id=client_one.id,
            service_id=service.id,
            date=appointment_date,
            start_time=time(10, 0),
        ),
        barber,
    )

    response = client.post(
        "/api/v1/appointments/",
        json={
            "barber_id": barber.id,
            "client_id": client_two.id,
            "service_id": service.id,
            "date": appointment_date.isoformat(),
            "start_time": "10:00:00",
        },
    )

    assert response.status_code == 409
    assert_error_shape(response.json(), "conflict")


def test_401_uses_standard_error_format(client_without_auth_override):
    response = client_without_auth_override.get("/api/v1/users/me")

    assert response.status_code == 401
    assert_error_shape(response.json(), "unauthorized")


def test_403_uses_standard_error_format(client):
    from app.api.deps import get_current_user
    from app.models.user import User

    def override_barber_user():
        return User(
            id=10,
            name="Barber",
            email="barber-error@test.com",
            role="barber",
            is_active=True,
        )

    app.dependency_overrides[get_current_user] = override_barber_user

    response = client.get("/api/v1/users/")

    assert response.status_code == 403
    assert_error_shape(response.json(), "forbidden")


def test_429_uses_standard_error_format(client):
    from app.core.rate_limit import reset_rate_limits

    reset_rate_limits()
    for _ in range(settings.LOGIN_RATE_LIMIT_REQUESTS):
        client.post(
            "/api/v1/auth/login",
            data={"username": "missing@test.com", "password": "badpass"},
        )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "missing@test.com", "password": "badpass"},
    )

    assert response.status_code == 429
    assert_error_shape(response.json(), "rate_limited")
    reset_rate_limits()


def test_500_does_not_leak_details_in_production(client_no_raise, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")

    response = client_no_raise.get("/__test__/unexpected-error")

    assert response.status_code == 500
    data = response.json()
    assert_error_shape(data, "internal_error")
    assert data["details"] == {}
    assert "secret" not in data["message"].lower()
    assert "password" not in str(data).lower()
    assert "token" not in str(data).lower()


def test_x_request_id_is_present(client):
    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
