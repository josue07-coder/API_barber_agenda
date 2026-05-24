from app.core.rate_limit import reset_rate_limits


def test_register_first_admin_allowed_and_second_blocked(client):
    first_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Admin",
            "email": "admin@test.com",
            "password": "test1234",
        },
    )

    assert first_response.status_code == 200
    assert first_response.json()["token_type"] == "bearer"

    second_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Admin Two",
            "email": "admin2@test.com",
            "password": "test1234",
        },
    )

    assert second_response.status_code == 403


def test_create_barber_returns_user(client):
    response = client.post(
        "/api/v1/auth/barbers",
        json={
            "name": "Barber",
            "email": "barber@test.com",
            "password": "test1234",
        },
        headers={"Authorization": "Bearer testtoken"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "barber@test.com"
    assert data["role"] == "barber"
    assert "access_token" not in data


def test_login_rate_limit(client):
    reset_rate_limits()

    for _ in range(5):
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "missing@test.com", "password": "badpass"},
        )
        assert response.status_code == 400

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "missing@test.com", "password": "badpass"},
    )

    assert response.status_code == 429
    reset_rate_limits()
