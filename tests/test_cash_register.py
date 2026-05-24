from datetime import date, datetime, timedelta, time, timezone

from app.api.deps import get_current_user
from app.main import app


def make_branch(db, name="Cash Branch"):
    from app.models.branch import Branch

    branch = Branch(name=name, is_active=True)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_user(db, role="barber", branch=None, email="cash-user@test.com"):
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


def make_client_service_appointment(db, branch, barber):
    from app.models.appointment import Appointment
    from app.models.client import Client
    from app.models.service import Service

    client_model = Client(name="Cash Client", phone=f"809888{branch.id:04d}", is_active=True)
    service = Service(
        name=f"Cash Service {branch.id}",
        duration_minutes=30,
        price=100,
        branch_id=branch.id,
        is_active=True,
    )
    db.add_all([client_model, service])
    db.commit()
    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        branch_id=branch.id,
        date=date.today() + timedelta(days=1),
        start_time=time(10, 0),
        end_time=time(10, 30),
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


def open_session(client, branch_id, amount="100.00"):
    return client.post(
        "/api/v1/cash-sessions/open",
        json={
            "branch_id": branch_id,
            "opening_amount": amount,
            "notes": "Apertura",
        },
    )


def test_open_cash_session(client, db):
    branch = make_branch(db, "Cash Open")

    response = open_session(client, branch.id)

    assert response.status_code == 200
    assert response.json()["branch_id"] == branch.id
    assert response.json()["status"] == "open"


def test_prevent_two_open_sessions(client, db):
    branch = make_branch(db, "Cash Duplicate")

    first = open_session(client, branch.id)
    second = open_session(client, branch.id)

    assert first.status_code == 200
    assert second.status_code == 409


def test_manual_income_expense_and_close_expected_difference(client, db):
    branch = make_branch(db, "Cash Close")
    session = open_session(client, branch.id, "100.00").json()
    income = client.post(
        "/api/v1/cash-movements/",
        json={
            "cash_session_id": session["id"],
            "movement_type": "income",
            "amount": "50.00",
            "method": "cash",
            "description": "Venta manual",
        },
    )
    expense = client.post(
        "/api/v1/cash-movements/",
        json={
            "cash_session_id": session["id"],
            "movement_type": "expense",
            "amount": "20.00",
            "method": "cash",
            "description": "Compra menor",
        },
    )
    close = client.patch(
        f"/api/v1/cash-sessions/{session['id']}/close",
        json={"closing_amount": "140.00"},
    )

    assert income.status_code == 200
    assert expense.status_code == 200
    assert close.status_code == 200
    assert close.json()["expected_amount"] == 130
    assert close.json()["difference_amount"] == 10


def test_no_movement_on_closed_session(client, db):
    branch = make_branch(db, "Cash Closed")
    session = open_session(client, branch.id).json()
    client.patch(
        f"/api/v1/cash-sessions/{session['id']}/close",
        json={"closing_amount": "100.00"},
    )

    response = client.post(
        "/api/v1/cash-movements/",
        json={
            "cash_session_id": session["id"],
            "movement_type": "income",
            "amount": "10.00",
            "method": "cash",
        },
    )

    assert response.status_code == 400


def test_cash_payment_creates_income_movement(client, db):
    branch = make_branch(db, "Cash Payment")
    barber = make_user(db, "barber", branch, "cash-payment@test.com")
    appointment = make_client_service_appointment(db, branch, barber)
    session = open_session(client, branch.id).json()

    payment = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": appointment.id,
            "amount": "40.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    )
    movements = client.get(f"/api/v1/cash-movements/session/{session['id']}")

    assert payment.status_code == 200
    assert movements.status_code == 200
    assert len(movements.json()) == 1
    assert movements.json()[0]["movement_type"] == "income"
    assert movements.json()[0]["payment_id"] == payment.json()["id"]


def test_cash_refund_creates_refund_movement(client, db):
    branch = make_branch(db, "Cash Refund")
    barber = make_user(db, "barber", branch, "cash-refund@test.com")
    appointment = make_client_service_appointment(db, branch, barber)
    session = open_session(client, branch.id).json()
    payment = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": appointment.id,
            "amount": "40.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    ).json()

    refund = client.patch(
        f"/api/v1/payments/{payment['id']}/refund",
        json={"reason": "Reembolso cash"},
    )
    movements = client.get(f"/api/v1/cash-movements/session/{session['id']}")

    assert refund.status_code == 200
    types = [item["movement_type"] for item in movements.json()]
    assert types == ["income", "refund"]


def test_barber_can_manage_only_own_branch_cash(client, db):
    own_branch = make_branch(db, "Cash Own")
    other_branch = make_branch(db, "Cash Other")
    barber = make_user(db, "barber", own_branch, "cash-own@test.com")

    def override_barber():
        return barber

    app.dependency_overrides[get_current_user] = override_barber

    own = open_session(client, own_branch.id)
    other = open_session(client, other_branch.id)

    assert own.status_code == 200
    assert other.status_code == 403


def test_payment_cash_without_open_session_is_rejected(client, db):
    branch = make_branch(db, "Cash Missing")
    barber = make_user(db, "barber", branch, "cash-missing@test.com")
    appointment = make_client_service_appointment(db, branch, barber)

    response = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": appointment.id,
            "amount": "40.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    )

    assert response.status_code == 409
