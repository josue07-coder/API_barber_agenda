from datetime import date, datetime, timedelta, time, timezone

from app.api.deps import get_current_user
from app.main import app


def make_branch(db, name="Settings Branch"):
    from app.models.branch import Branch

    branch = Branch(name=name, is_active=True)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_barber(db, branch, email="settings-barber@test.com"):
    from app.models.user import User

    barber = User(
        name="Settings Barber",
        email=email,
        password="x",
        role="barber",
        branch_id=branch.id,
        is_active=True,
    )
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber


def make_client(db, phone="8097771000"):
    from app.models.client import Client
    from app.models.user import User

    client_model = Client(name="Settings Client", phone=phone, is_active=True)
    db.add(client_model)
    db.commit()
    user = User(
        name="Settings Client",
        email=f"{phone}@client.test",
        password="x",
        role="client",
        client_id=client_model.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, client_model


def make_service_schedule(db, branch, barber, target_date, price=100):
    from app.models.barber_schedule import BarberSchedule
    from app.models.service import Service

    service = Service(
        name=f"Settings Service {price}",
        duration_minutes=30,
        price=price,
        branch_id=branch.id,
        is_active=True,
    )
    schedule = BarberSchedule(
        barber_id=barber.id,
        weekday=target_date.weekday(),
        start_time=time(8, 0),
        end_time=time(20, 0),
        is_active=True,
    )
    db.add_all([service, schedule])
    db.commit()
    return service


def create_direct_appointment(db, branch, barber, client_model, service, appt_dt):
    from app.models.appointment import Appointment

    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        branch_id=branch.id,
        date=appt_dt.date(),
        start_time=appt_dt.time().replace(microsecond=0),
        end_time=(appt_dt + timedelta(minutes=30)).time().replace(microsecond=0),
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


def update_settings(client, branch_id, **overrides):
    payload = {
        "timezone": "America/Santo_Domingo",
        "currency": "USD",
        "default_cancel_cutoff_hours": 6,
        "default_reschedule_cutoff_hours": 6,
        "deposit_required": False,
        "default_deposit_amount": None,
        "default_deposit_percentage": None,
        "reminder_24h_enabled": True,
        "reminder_2h_enabled": True,
    }
    payload.update(overrides)
    return client.put(f"/api/v1/branches/{branch_id}/settings", json=payload)


def test_admin_updates_and_reads_branch_settings(client, db):
    branch = make_branch(db, "Settings Admin")

    response = update_settings(
        client,
        branch.id,
        default_cancel_cutoff_hours=4,
        deposit_required=True,
        default_deposit_amount="20.00",
    )
    read_response = client.get(f"/api/v1/branches/{branch.id}/settings")

    assert response.status_code == 200
    assert response.json()["default_cancel_cutoff_hours"] == 4
    assert response.json()["deposit_required"] is True
    assert read_response.status_code == 200


def test_barber_reads_only_own_branch_settings(client, db):
    own_branch = make_branch(db, "Settings Own")
    other_branch = make_branch(db, "Settings Other")
    barber = make_barber(db, own_branch, "settings-own@test.com")

    def override_barber():
        return barber

    app.dependency_overrides[get_current_user] = override_barber

    own = client.get(f"/api/v1/branches/{own_branch.id}/settings")
    other = client.get(f"/api/v1/branches/{other_branch.id}/settings")
    update = client.put(f"/api/v1/branches/{own_branch.id}/settings", json={})

    assert own.status_code == 200
    assert other.status_code == 403
    assert update.status_code == 403


def test_branch_settings_cutoff_overrides_global(client, db):
    branch = make_branch(db, "Settings Cutoff")
    barber = make_barber(db, branch, "settings-cutoff@test.com")
    client_user, client_model = make_client(db, "8097771001")
    appt_dt = datetime.now() + timedelta(hours=5)
    service = make_service_schedule(db, branch, barber, appt_dt.date())
    appointment = create_direct_appointment(db, branch, barber, client_model, service, appt_dt)
    update_settings(client, branch.id, default_cancel_cutoff_hours=6)
    app.dependency_overrides[get_current_user] = override_user(client_user)

    blocked = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert blocked.status_code == 409


def test_branch_settings_currency_and_deposit_required(client, db):
    branch = make_branch(db, "Settings Deposit")
    barber = make_barber(db, branch, "settings-deposit@test.com")
    _, client_model = make_client(db, "8097771002")
    appt_dt = datetime.now() + timedelta(days=3)
    service = make_service_schedule(db, branch, barber, appt_dt.date(), price=100)
    appointment = create_direct_appointment(db, branch, barber, client_model, service, appt_dt)
    update_settings(
        client,
        branch.id,
        currency="USD",
        deposit_required=True,
        default_deposit_percentage="50.00",
    )
    client.post(
        "/api/v1/cash-sessions/open",
        json={
            "branch_id": branch.id,
            "opening_amount": "0.00",
        },
    )

    too_low = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": appointment.id,
            "amount": "25.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    )
    valid = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": appointment.id,
            "amount": "50.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    )

    assert too_low.status_code == 400
    assert valid.status_code == 200
    assert valid.json()["currency"] == "USD"


def test_branch_settings_disable_2h_reminders(client, db):
    branch = make_branch(db, "Settings Reminders")
    barber = make_barber(db, branch, "settings-reminder@test.com")
    _, client_model = make_client(db, "8097771003")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    service = make_service_schedule(db, branch, barber, now.date())
    create_direct_appointment(db, branch, barber, client_model, service, now + timedelta(hours=1))
    update_settings(client, branch.id, reminder_2h_enabled=False)

    response = client.post("/api/v1/notifications/generate-reminders")
    notifications = client.get("/api/v1/notifications/").json()

    assert response.status_code == 200
    assert response.json()["created"] == 2
    assert all(item["subject"] != "appointment_reminder_2h" for item in notifications)
    assert any(item["subject"] == "appointment_reminder_24h" for item in notifications)
