from datetime import date, time, timedelta
from itertools import count

from app.api.deps import get_current_user
from app.main import app


PHONE_COUNTER = count(8097000000)


def make_branch(db, name="Penalty Branch"):
    from app.models.branch import Branch

    branch = Branch(name=name, is_active=True)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_user(db, *, role="barber", email="penalty-barber@test.com", branch=None, client_id=None):
    from app.models.user import User

    user = User(
        name=email.split("@")[0],
        email=email,
        password="x",
        role=role,
        branch_id=branch.id if branch else None,
        client_id=client_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_client(db, name="Penalty Client"):
    from app.models.client import Client

    client = Client(name=name, phone=str(next(PHONE_COUNTER)), is_active=True)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def make_service(db, branch=None, name="Penalty Service", price=100):
    from app.models.service import Service

    service = Service(
        name=name,
        duration_minutes=30,
        price=price,
        branch_id=branch.id if branch else None,
        is_active=True,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


def make_appointment(db, barber, client_model, service, branch=None, *, days=2):
    from app.models.appointment import Appointment

    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        branch_id=branch.id if branch else None,
        date=date.today() + timedelta(days=days),
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


def test_no_show_generates_penalty_and_notification(client, db):
    branch = make_branch(db, "Penalty No Show")
    barber = make_user(db, email="penalty-noshow@test.com", branch=branch)
    client_model = make_client(db)
    service = make_service(db, branch=branch)
    appointment = make_appointment(db, barber, client_model, service, branch=branch)

    response = client.patch(f"/api/v1/appointments/{appointment.id}/no-show")
    penalties = client.get(f"/api/v1/clients/{client_model.id}/penalties")
    notifications = client.get("/api/v1/notifications/")

    assert response.status_code == 200
    assert penalties.status_code == 200
    assert penalties.json()[0]["penalty_type"] == "no_show"
    assert penalties.json()[0]["points"] == 3
    assert any(item["related_type"] == "penalty" for item in notifications.json())


def test_late_cancel_generates_penalty_when_client_is_inside_cutoff(client, db):
    branch = make_branch(db, "Penalty Late Cancel")
    barber = make_user(db, email="penalty-late-barber@test.com", branch=branch)
    client_model = make_client(db)
    client_user = make_user(db, role="client", email="penalty-late-client@test.com", client_id=client_model.id)
    service = make_service(db, branch=branch)
    appointment = make_appointment(db, barber, client_model, service, branch=branch, days=1)

    app.dependency_overrides[get_current_user] = override_user(client_user)
    response = client.patch(
        f"/api/v1/appointments/{appointment.id}/cancel",
        json={"reason": "No podre asistir"},
    )

    app.dependency_overrides[get_current_user] = override_user(make_user(db, role="admin", email="penalty-admin-late@test.com"))
    penalties = client.get(f"/api/v1/clients/{client_model.id}/penalties")

    assert response.status_code == 409
    assert penalties.status_code == 200
    assert penalties.json()[0]["penalty_type"] == "late_cancel"


def test_client_with_exceeded_penalty_points_cannot_book(client, db, monkeypatch):
    monkeypatch.setattr("app.services.client_penalty_service.settings.CLIENT_MAX_ACTIVE_PENALTY_POINTS", 1)
    branch = make_branch(db, "Penalty Block")
    barber = make_user(db, email="penalty-block-barber@test.com", branch=branch)
    client_model = make_client(db)
    client_user = make_user(db, role="client", email="penalty-block-client@test.com", client_id=client_model.id)
    service = make_service(db, branch=branch)

    manual = client.post(
        f"/api/v1/clients/{client_model.id}/penalties",
        json={"penalty_type": "manual", "reason": "Riesgo", "points": 2},
    )
    app.dependency_overrides[get_current_user] = override_user(client_user)
    response = client.post(
        "/api/v1/appointments/",
        json={
            "barber_id": barber.id,
            "client_id": client_model.id,
            "service_id": service.id,
            "branch_id": branch.id,
            "date": (date.today() + timedelta(days=3)).isoformat(),
            "start_time": "10:00:00",
        },
    )

    assert manual.status_code == 200
    assert response.status_code == 403


def test_admin_forgives_penalty_and_mark_paid(client, db):
    client_model = make_client(db)
    penalty = client.post(
        f"/api/v1/clients/{client_model.id}/penalties",
        json={"penalty_type": "manual", "reason": "Manual", "points": 1, "amount": "50.00"},
    ).json()

    forgiven = client.patch(f"/api/v1/penalties/{penalty['id']}/forgive", json={"reason": "Cortesia"})
    second = client.post(
        f"/api/v1/clients/{client_model.id}/penalties",
        json={"penalty_type": "manual", "reason": "Monto pendiente", "points": 1, "amount": "50.00"},
    ).json()
    paid = client.patch(f"/api/v1/penalties/{second['id']}/mark-paid", json={"reason": "Pagada en caja"})

    assert forgiven.status_code == 200
    assert forgiven.json()["status"] == "forgiven"
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"


def test_client_only_sees_own_penalties(client, db):
    own_client = make_client(db, "Own Penalty Client")
    other_client = make_client(db, "Other Penalty Client")
    own_user = make_user(db, role="client", email="penalty-own@test.com", client_id=own_client.id)
    client.post(
        f"/api/v1/clients/{own_client.id}/penalties",
        json={"penalty_type": "manual", "reason": "Propia", "points": 1},
    )
    client.post(
        f"/api/v1/clients/{other_client.id}/penalties",
        json={"penalty_type": "manual", "reason": "Ajena", "points": 1},
    )

    app.dependency_overrides[get_current_user] = override_user(own_user)
    own = client.get("/api/v1/me/penalties")
    other = client.get(f"/api/v1/clients/{other_client.id}/penalties")

    assert own.status_code == 200
    assert len(own.json()) == 1
    assert other.status_code == 403


def test_barber_sees_penalties_related_to_own_appointments(client, db):
    branch = make_branch(db, "Penalty Barber")
    barber = make_user(db, email="penalty-barber-own@test.com", branch=branch)
    client_model = make_client(db)
    service = make_service(db, branch=branch)
    appointment = make_appointment(db, barber, client_model, service, branch=branch)
    client.patch(f"/api/v1/appointments/{appointment.id}/no-show")

    app.dependency_overrides[get_current_user] = override_user(barber)
    response = client.get(f"/api/v1/clients/{client_model.id}/penalties")

    assert response.status_code == 200
    assert response.json()[0]["penalty_type"] == "no_show"


def test_penalty_report(client, db):
    branch = make_branch(db, "Penalty Report")
    barber = make_user(db, email="penalty-report@test.com", branch=branch)
    client_model = make_client(db)
    service = make_service(db, branch=branch)
    appointment = make_appointment(db, barber, client_model, service, branch=branch)
    client.patch(f"/api/v1/appointments/{appointment.id}/no-show")

    response = client.get(
        "/api/v1/reports/clients/penalties",
        params={
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["top_no_show_clients"][0]["client_id"] == client_model.id
    assert data["by_status"][0]["status"] == "active"
    assert data["by_branch"][0]["branch_id"] == branch.id
