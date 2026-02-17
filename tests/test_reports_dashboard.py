def test_dashboard_empty(db, client, admin_token):
        response = client.get(
    "/api/v1/reports/dashboard?start_date=2026-01-01&end_date=2026-01-31",
    headers={"Authorization": f"Bearer {admin_token}"}
)

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert data["ingresos"] == 0