from datetime import date, datetime, time, timedelta, timezone
from itertools import count

from app.api.deps import get_current_user
from app.main import app


PHONE_COUNTER = count(8098000000)


def make_branch(db, name="Dashboard Branch"):
    from app.models.branch import Branch

    branch = Branch(name=name, is_active=True)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_user(db, *, role="barber", email="dashboard-user@test.com", branch=None):
    from app.models.user import User

    user = User(
        name=email.split("@")[0],
        email=email,
        password="x",
        role=role,
        branch_id=branch.id if branch else None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_client(db, name="Dashboard Client"):
    from app.models.client import Client

    client = Client(name=name, phone=str(next(PHONE_COUNTER)), is_active=True)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def make_service(db, branch, name="Dashboard Service", price=100):
    from app.models.service import Service

    service = Service(name=name, duration_minutes=30, price=price, branch_id=branch.id, is_active=True)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def make_appointment(db, *, barber, client_model, service, branch, day=None, status="completada", start=time(10, 0)):
    from app.models.appointment import Appointment

    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        branch_id=branch.id,
        date=day or date.today(),
        start_time=start,
        end_time=time(start.hour, 30),
        status=status,
        payment_status="paid",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def add_payment(db, appointment, amount=100, method="card", status="paid"):
    from app.models.payment import Payment

    payment = Payment(
        appointment_id=appointment.id,
        client_id=appointment.client_id,
        amount=amount,
        currency="DOP",
        payment_method=method,
        status=status,
        paid_at=datetime.now(timezone.utc) if status in {"paid", "partially_paid"} else None,
        refunded_at=datetime.now(timezone.utc) if status == "refunded" else None,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def add_commission(db, appointment, payment, amount=10, status="pending"):
    from app.models.barber_commission import BarberCommission

    commission = BarberCommission(
        appointment_id=appointment.id,
        payment_id=payment.id,
        barber_id=appointment.user_id,
        branch_id=appointment.branch_id,
        service_id=appointment.service_id,
        base_amount=payment.amount,
        commission_amount=amount,
        status=status,
    )
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


def override_user(user):
    def _override():
        return user

    return _override


def seed_dashboard(db):
    branch_one = make_branch(db, "Dashboard One")
    branch_two = make_branch(db, "Dashboard Two")
    barber_one = make_user(db, email="dashboard-barber-one@test.com", branch=branch_one)
    barber_two = make_user(db, email="dashboard-barber-two@test.com", branch=branch_two)
    client_one = make_client(db, "Dashboard Client One")
    client_two = make_client(db, "Dashboard Client Two")
    service_one = make_service(db, branch_one, "Corte Dashboard", 100)
    service_two = make_service(db, branch_two, "Barba Dashboard", 200)

    today = date.today()
    appt_one = make_appointment(db, barber=barber_one, client_model=client_one, service=service_one, branch=branch_one, day=today, status="completada")
    appt_two = make_appointment(db, barber=barber_two, client_model=client_two, service=service_two, branch=branch_two, day=today, status="cancelada", start=time(11, 0))
    appt_three = make_appointment(db, barber=barber_one, client_model=client_one, service=service_one, branch=branch_one, day=today + timedelta(days=1), status="no_show", start=time(12, 0))
    payment = add_payment(db, appt_one, amount=100, method="card")
    add_payment(db, appt_two, amount=50, method="cash", status="refunded")
    add_commission(db, appt_one, payment, amount=15, status="pending")
    return {
        "branch_one": branch_one,
        "branch_two": branch_two,
        "barber_one": barber_one,
        "barber_two": barber_two,
        "client_one": client_one,
        "appt_one": appt_one,
        "appt_three": appt_three,
    }


def params(extra=None):
    payload = {
        "start_date": date.today().isoformat(),
        "end_date": (date.today() + timedelta(days=1)).isoformat(),
    }
    if extra:
        payload.update(extra)
    return payload


def test_dashboard_overview_admin(client, db):
    seed_dashboard(db)

    response = client.get("/api/v1/dashboard/overview", params=params())

    assert response.status_code == 200
    data = response.json()
    assert data["totals"]["total_appointments"] == 3
    assert data["totals"]["completed_appointments"] == 1
    assert data["totals"]["total_revenue"] == 100.0
    assert data["top_services"][0]["label"] == "Corte Dashboard"


def test_dashboard_overview_barber_limited(client, db):
    data = seed_dashboard(db)
    app.dependency_overrides[get_current_user] = override_user(data["barber_one"])

    response = client.get("/api/v1/dashboard/overview", params=params())

    assert response.status_code == 200
    payload = response.json()
    assert payload["totals"]["total_appointments"] == 2
    assert all(item["id"] == data["barber_one"].id for item in payload["top_barbers"])


def test_dashboard_client_forbidden(client, db):
    client_user = make_user(db, role="client", email="dashboard-client-user@test.com")
    app.dependency_overrides[get_current_user] = override_user(client_user)

    response = client.get("/api/v1/dashboard/overview", params=params())

    assert response.status_code == 403


def test_dashboard_filters_by_branch_and_barber(client, db):
    data = seed_dashboard(db)

    by_branch = client.get("/api/v1/dashboard/overview", params=params({"branch_id": data["branch_one"].id}))
    by_barber = client.get("/api/v1/dashboard/overview", params=params({"barber_id": data["barber_two"].id}))

    assert by_branch.status_code == 200
    assert by_branch.json()["totals"]["total_appointments"] == 2
    assert by_barber.status_code == 200
    assert by_barber.json()["totals"]["total_appointments"] == 1


def test_dashboard_financial_uses_payments(client, db):
    seed_dashboard(db)

    response = client.get("/api/v1/dashboard/financial", params=params())

    assert response.status_code == 200
    data = response.json()
    assert data["card_income"] == 100.0
    assert data["refunds"] == 50.0
    assert data["net_revenue"] == 50.0
    assert data["commissions_pending"] == 15.0


def test_dashboard_appointments_rates(client, db):
    seed_dashboard(db)

    response = client.get("/api/v1/dashboard/appointments", params=params())

    assert response.status_code == 200
    data = response.json()
    assert data["cancellation_rate"] == 33.33
    assert data["no_show_rate"] == 33.33
    assert data["average_appointments_per_day"] == 1.5


def test_dashboard_barbers_revenue_and_commissions(client, db):
    data = seed_dashboard(db)

    response = client.get("/api/v1/dashboard/barbers", params=params())

    assert response.status_code == 200
    payload = response.json()
    revenue = {item["barber_id"]: item["value"] for item in payload["revenue_per_barber"]}
    commissions = {item["barber_id"]: item["value"] for item in payload["commissions_per_barber"]}
    assert revenue[data["barber_one"].id] == 100.0
    assert commissions[data["barber_one"].id] == 15.0


def test_dashboard_clients_top_clients(client, db):
    data = seed_dashboard(db)

    response = client.get("/api/v1/dashboard/clients", params=params())

    assert response.status_code == 200
    payload = response.json()
    assert payload["top_clients_by_visits"][0]["id"] == data["client_one"].id
    assert payload["top_clients_by_revenue"][0]["value"] == 100.0


def test_dashboard_branches_comparison(client, db):
    data = seed_dashboard(db)

    response = client.get("/api/v1/dashboard/branches", params=params())

    assert response.status_code == 200
    comparison = {item["branch_id"]: item for item in response.json()["branch_comparison"]}
    assert comparison[data["branch_one"].id]["revenue"] == 100.0
    assert comparison[data["branch_one"].id]["appointments"] == 2
