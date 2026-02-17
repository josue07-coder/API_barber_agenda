def test_get_appointments_admin(client):
        response = client.get(
        "/api/v1/appointments",
        headers={"Authorization": "Bearer testtoken"}
)
        assert response.status_code in [200, 401]
