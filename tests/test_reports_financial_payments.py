from datetime import date, datetime, time, timezone

from app.api.deps import get_current_user
from app.main import app


def make_financial_data(db):
    from app.models.appointment import Appointment
    from app.models.client import Client
    from app.models.payment import Payment
    from app.models.service import Service
    from app.models.user import User

    barber = User(
        name="Barber Finance",
        email="barber-finance@test.com",
        password="x",
        role="barber",
        is_active=True,
    )
    other_barber = User(
        name="Other Finance",
        email="other-finance@test.com",
        password="x",
        role="barber",
        is_active=True,
    )
    client_model = Client(name="Cliente Finanzas", phone="111", is_active=True)
    service = Service(name="Corte Finanzas", duration_minutes=30, price=100, is_active=True)
    db.add_all([barber, other_barber, client_model, service])
    db.commit()

    today = date.today()
    appointment_paid = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        date=today,
        start_time=time(10, 0),
        end_time=time(10, 30),
        status="completada",
        payment_status="paid",
    )
    appointment_pending = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        date=today,
        start_time=time(11, 0),
        end_time=time(11, 30),
        status="agendada",
        payment_status="partially_paid",
    )
    appointment_other = Appointment(
        user_id=other_barber.id,
        client_id=client_model.id,
        service_id=service.id,
        date=today,
        start_time=time(12, 0),
        end_time=time(12, 30),
        status="completada",
        payment_status="paid",
    )
    db.add_all([appointment_paid, appointment_pending, appointment_other])
    db.commit()

    now = datetime.now(timezone.utc)
    db.add_all([
        Payment(
            appointment_id=appointment_paid.id,
            client_id=client_model.id,
            amount=80,
            currency="DOP",
            payment_method="cash",
            status="paid",
            paid_at=now,
        ),
        Payment(
            appointment_id=appointment_pending.id,
            client_id=client_model.id,
            amount=25,
            currency="DOP",
            payment_method="card",
            status="pending",
        ),
        Payment(
            appointment_id=appointment_pending.id,
            client_id=client_model.id,
            amount=40,
            currency="DOP",
            payment_method="card",
            status="paid",
            paid_at=now,
        ),
        Payment(
            appointment_id=appointment_paid.id,
            client_id=client_model.id,
            amount=10,
            currency="DOP",
            payment_method="cash",
            status="refunded",
            refunded_at=now,
        ),
        Payment(
            appointment_id=appointment_other.id,
            client_id=client_model.id,
            amount=60,
            currency="DOP",
            payment_method="transfer",
            status="paid",
            paid_at=now,
        ),
    ])
    db.commit()
    return barber, other_barber, today


def test_dashboard_uses_paid_payments_and_reports_refunds(client, db, admin_token):
    _, _, today = make_financial_data(db)

    response = client.get(
        f"/api/v1/reports/dashboard?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ingresos"] == 180.0
    assert data["total_reembolsado"] == 10.0
    assert data["balance_neto"] == 170.0


def test_pending_payments_do_not_sum_and_income_by_method(client, db, admin_token):
    _, _, today = make_financial_data(db)

    response = client.get(
        f"/api/v1/reports/financial/by-method?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    methods = {item["payment_method"]: item["ingresos"] for item in response.json()}
    assert methods["cash"] == 80.0
    assert methods["card"] == 40.0
    assert methods["transfer"] == 60.0


def test_daily_and_monthly_income_reports(client, db, admin_token):
    _, _, today = make_financial_data(db)

    daily = client.get(
        f"/api/v1/reports/financial/daily?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    monthly = client.get(
        f"/api/v1/reports/financial/monthly?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert daily.status_code == 200
    assert monthly.status_code == 200
    assert daily.json()[0]["ingresos"] == 180.0
    assert daily.json()[0]["reembolsos"] == 10.0
    assert monthly.json()[0]["period"] == today.strftime("%Y-%m")
    assert monthly.json()[0]["balance_neto"] == 170.0


def test_pending_balances_report(client, db, admin_token):
    _, _, today = make_financial_data(db)

    response = client.get(
        f"/api/v1/reports/financial/pending-balances?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    balances = {item["appointment_id"]: item["pending_balance"] for item in response.json()}
    assert 20.0 in balances.values()
    assert 60.0 in balances.values()


def test_barber_financial_report_only_returns_own_income(client, db):
    barber, _, today = make_financial_data(db)

    def override_barber():
        return barber

    app.dependency_overrides[get_current_user] = override_barber

    response = client.get(
        f"/api/v1/reports/financial/by-barber?start_date={today}&end_date={today}"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["barber_id"] == barber.id
    assert data[0]["ingresos"] == 120.0


def test_payment_export_contains_financial_columns(client, db, admin_token):
    _, _, today = make_financial_data(db)

    response = client.get(
        f"/api/v1/reports/financial/by-barber/export/csv?start_date={today}&end_date={today}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    content = response.text
    assert "fecha,cita,cliente,barbero,servicio,metodo_pago,monto_pagado,monto_reembolsado,balance_neto,estado_pago" in content
    assert "refunded" in content
