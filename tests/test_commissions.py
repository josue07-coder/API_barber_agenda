from datetime import date, time, timedelta
from itertools import count

from app.api.deps import get_current_user
from app.main import app


PHONE_COUNTER = count(8096000000)


def make_branch(db, name="Commission Branch"):
    from app.models.branch import Branch

    branch = Branch(name=name, is_active=True)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_user(db, *, role="barber", email="commission-barber@test.com", branch=None):
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


def make_appointment(db, barber, branch=None, *, price=100, service_name="Commission Service"):
    from app.models.appointment import Appointment
    from app.models.client import Client
    from app.models.service import Service

    client_model = Client(name="Commission Client", phone=str(next(PHONE_COUNTER)), is_active=True)
    service = Service(
        name=service_name,
        duration_minutes=30,
        price=price,
        branch_id=branch.id if branch else None,
        is_active=True,
    )
    db.add_all([client_model, service])
    db.commit()
    db.refresh(service)

    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        branch_id=branch.id if branch else None,
        date=date.today() + timedelta(days=2),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status="agendada",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment, service


def payment_payload(appointment_id, *, amount="100.00", status="paid"):
    return {
        "appointment_id": appointment_id,
        "amount": amount,
        "currency": "DOP",
        "payment_method": "card",
        "status": status,
    }


def create_rule(client, barber, *, branch=None, service=None, commission_type="percentage", value="10.00"):
    return client.post(
        "/api/v1/commissions/rules",
        json={
            "barber_id": barber.id,
            "branch_id": branch.id if branch else None,
            "service_id": service.id if service else None,
            "commission_type": commission_type,
            "commission_value": value,
        },
    )


def override_user(user):
    def _override():
        return user

    return _override


def test_create_percentage_commission_rule(client, db):
    barber = make_user(db, email="commission-rule-percentage@test.com")

    response = create_rule(client, barber, commission_type="percentage", value="15.00")

    assert response.status_code == 200
    assert response.json()["commission_type"] == "percentage"
    assert float(response.json()["commission_value"]) == 15.0


def test_create_fixed_commission_rule(client, db):
    barber = make_user(db, email="commission-rule-fixed@test.com")

    response = create_rule(client, barber, commission_type="fixed", value="25.00")

    assert response.status_code == 200
    assert response.json()["commission_type"] == "fixed"
    assert float(response.json()["commission_value"]) == 25.0


def test_generate_commission_when_payment_is_paid(client, db):
    barber = make_user(db, email="commission-payment@test.com")
    appointment, _ = make_appointment(db, barber, price=200)
    create_rule(client, barber, commission_type="percentage", value="10.00")

    payment = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="200.00"))
    commissions = client.get("/api/v1/commissions/")

    assert payment.status_code == 200
    assert commissions.status_code == 200
    assert len(commissions.json()) == 1
    assert commissions.json()[0]["payment_id"] == payment.json()["id"]
    assert float(commissions.json()[0]["commission_amount"]) == 20.0


def test_service_rule_has_priority_over_branch_fallback(client, db):
    branch = make_branch(db, "Commission Priority")
    barber = make_user(db, email="commission-priority@test.com", branch=branch)
    appointment, service = make_appointment(db, barber, branch=branch, price=100)
    create_rule(client, barber, branch=branch, commission_type="percentage", value="5.00")
    create_rule(client, barber, branch=branch, service=service, commission_type="percentage", value="20.00")

    client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="100.00"))
    commissions = client.get("/api/v1/commissions/")

    assert commissions.status_code == 200
    assert float(commissions.json()[0]["commission_amount"]) == 20.0


def test_do_not_duplicate_commission_for_same_payment(client, db):
    barber = make_user(db, email="commission-no-duplicate@test.com")
    appointment, _ = make_appointment(db, barber, price=100)
    create_rule(client, barber, commission_type="percentage", value="10.00")
    payment = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="100.00")).json()

    mark_paid = client.patch(f"/api/v1/payments/{payment['id']}/mark-paid", json={})
    commissions = client.get("/api/v1/commissions/")

    assert mark_paid.status_code == 200
    assert len(commissions.json()) == 1


def test_refund_cancels_pending_commission(client, db):
    barber = make_user(db, email="commission-refund@test.com")
    appointment, _ = make_appointment(db, barber, price=100)
    create_rule(client, barber, commission_type="percentage", value="10.00")
    payment = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="100.00")).json()

    refund = client.patch(f"/api/v1/payments/{payment['id']}/refund", json={"reason": "Reembolso"})
    commissions = client.get("/api/v1/commissions/")

    assert refund.status_code == 200
    assert commissions.json()[0]["status"] == "cancelled"


def test_barber_only_sees_own_commissions(client, db):
    owner = make_user(db, email="commission-owner@test.com")
    other = make_user(db, email="commission-other@test.com")
    owner_appointment, _ = make_appointment(db, owner, price=100)
    other_appointment, _ = make_appointment(db, other, price=100)
    create_rule(client, owner, commission_type="percentage", value="10.00")
    create_rule(client, other, commission_type="percentage", value="10.00")
    client.post("/api/v1/payments/", json=payment_payload(owner_appointment.id, amount="100.00"))
    client.post("/api/v1/payments/", json=payment_payload(other_appointment.id, amount="100.00"))

    app.dependency_overrides[get_current_user] = override_user(owner)
    own = client.get("/api/v1/commissions/")
    forbidden = client.get(f"/api/v1/commissions/barber/{other.id}")

    assert own.status_code == 200
    assert len(own.json()) == 1
    assert own.json()[0]["barber_id"] == owner.id
    assert forbidden.status_code == 403


def test_admin_approves_and_marks_commission_paid(client, db):
    barber = make_user(db, email="commission-approve@test.com")
    appointment, _ = make_appointment(db, barber, price=100)
    create_rule(client, barber, commission_type="fixed", value="30.00")
    client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="100.00"))
    commission = client.get("/api/v1/commissions/").json()[0]

    approved = client.patch(f"/api/v1/commissions/{commission['id']}/approve")
    paid = client.patch(f"/api/v1/commissions/{commission['id']}/mark-paid")

    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
    assert paid.json()["paid_at"] is not None


def test_commission_summary(client, db):
    branch = make_branch(db, "Commission Summary")
    barber = make_user(db, email="commission-summary@test.com", branch=branch)
    appointment, _ = make_appointment(db, barber, branch=branch, price=100)
    create_rule(client, barber, branch=branch, commission_type="percentage", value="10.00")
    client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="100.00"))

    response = client.get("/api/v1/commissions/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["by_status"]["pending"]["count"] == 1
    assert data["by_status"]["pending"]["total"] == 10.0
    assert data["by_barber"][0]["barber_id"] == barber.id
    assert data["by_branch"][0]["branch_id"] == branch.id
