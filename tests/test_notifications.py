from datetime import date, datetime, timedelta, time, timezone

from app.api.deps import get_current_user
from app.main import app


def make_user(db, *, role="barber", email="notification-barber@test.com"):
    from app.models.user import User

    user = User(
        name=email.split("@")[0],
        email=email,
        password="x",
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def make_client_service(db):
    from app.models.client import Client
    from app.models.service import Service

    client_model = Client(name="Cliente Notificacion", phone="8091112222", is_active=True)
    service = Service(name="Corte Notificacion", duration_minutes=30, price=100, is_active=True)
    db.add_all([client_model, service])
    db.commit()
    return client_model, service


def add_schedule(db, barber, target_date):
    from app.models.barber_schedule import BarberSchedule

    db.add(
        BarberSchedule(
            barber_id=barber.id,
            weekday=target_date.weekday(),
            start_time=time(8, 0),
            end_time=time(20, 0),
            is_active=True,
        )
    )
    db.commit()


def create_valid_appointment(db, barber, *, appointment_date=None, start_time=time(10, 0)):
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment

    appointment_date = appointment_date or (date.today() + timedelta(days=3))
    client_model, service = make_client_service(db)
    add_schedule(db, barber, appointment_date)
    return create_new_appointment(
        db,
        AppointmentCreate(
            barber_id=barber.id,
            client_id=client_model.id,
            service_id=service.id,
            date=appointment_date,
            start_time=start_time,
        ),
        barber,
    )


def direct_appointment(db, barber, appt_dt):
    from app.models.appointment import Appointment

    client_model, service = make_client_service(db)
    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        date=appt_dt.date(),
        start_time=appt_dt.time().replace(microsecond=0),
        end_time=(appt_dt + timedelta(minutes=30)).time().replace(microsecond=0),
        status="confirmada",
        payment_status="pending",
    )
    db.add(appointment)
    db.commit()
    return appointment


def test_notification_created_for_appointment_created(db):
    from app.models.notification import Notification

    barber = make_user(db, email="notif-created@test.com")
    appointment = create_valid_appointment(db, barber)

    notification = (
        db.query(Notification)
        .filter(
            Notification.related_type == "appointment",
            Notification.related_id == appointment.id,
            Notification.subject == "appointment_created",
        )
        .first()
    )

    assert notification is not None
    assert notification.status == "pending"
    assert notification.channel == "in_app"


def test_notification_created_for_appointment_cancellation(client, db):
    barber = make_user(db, email="notif-cancel@test.com")
    appointment = create_valid_appointment(db, barber)

    response = client.patch(f"/api/v1/appointments/{appointment.id}/cancel")

    assert response.status_code == 200
    notifications = client.get("/api/v1/notifications/").json()
    subjects = [item["subject"] for item in notifications]
    assert "appointment_cancelled" in subjects


def test_notification_created_for_registered_payment(client, db):
    barber = make_user(db, email="notif-payment@test.com")
    appointment = create_valid_appointment(db, barber)

    response = client.post(
        "/api/v1/payments/",
        json={
            "appointment_id": appointment.id,
            "amount": "50.00",
            "currency": "DOP",
            "payment_method": "cash",
            "status": "paid",
        },
    )

    assert response.status_code == 200
    notifications = client.get("/api/v1/notifications/").json()
    subjects = [item["subject"] for item in notifications]
    assert "payment_registered" in subjects


def test_generate_24h_reminder(client, db):
    barber = make_user(db, email="notif-24h@test.com")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    direct_appointment(db, barber, now + timedelta(hours=23))

    response = client.post("/api/v1/notifications/generate-reminders")

    assert response.status_code == 200
    assert response.json()["created"] == 2
    notifications = client.get("/api/v1/notifications/").json()
    assert any(item["subject"] == "appointment_reminder_24h" for item in notifications)


def test_generate_2h_reminder(client, db):
    barber = make_user(db, email="notif-2h@test.com")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    direct_appointment(db, barber, now + timedelta(hours=1))

    response = client.post("/api/v1/notifications/generate-reminders")

    assert response.status_code == 200
    assert response.json()["created"] == 4
    notifications = client.get("/api/v1/notifications/").json()
    subjects = [item["subject"] for item in notifications]
    assert "appointment_reminder_24h" in subjects
    assert "appointment_reminder_2h" in subjects


def test_generate_reminders_does_not_duplicate(client, db):
    barber = make_user(db, email="notif-no-duplicate@test.com")
    now = datetime.now(timezone.utc).replace(microsecond=0)
    direct_appointment(db, barber, now + timedelta(hours=1))

    first = client.post("/api/v1/notifications/generate-reminders")
    second = client.post("/api/v1/notifications/generate-reminders")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["created"] == 4
    assert second.json()["created"] == 0


def test_mark_sent_failed_and_cancel_notification(client, db):
    barber = make_user(db, email="notif-states@test.com")
    create_valid_appointment(db, barber)
    notification = client.get("/api/v1/notifications/").json()[0]

    sent = client.patch(f"/api/v1/notifications/{notification['id']}/mark-sent")
    failed = client.patch(
        f"/api/v1/notifications/{notification['id']}/mark-failed",
        json={"error_message": "Fallo simulado"},
    )
    cancelled = client.patch(f"/api/v1/notifications/{notification['id']}/cancel")

    assert sent.status_code == 200
    assert sent.json()["status"] == "sent"
    assert failed.status_code == 200
    assert failed.json()["status"] == "failed"
    assert failed.json()["error_message"] == "Fallo simulado"
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def test_barber_can_only_access_related_notifications(client, db):
    owner = make_user(db, email="notif-owner@test.com")
    other = make_user(db, email="notif-other@test.com")
    appointment = create_valid_appointment(db, owner)

    def override_other_barber():
        return other

    app.dependency_overrides[get_current_user] = override_other_barber

    list_response = client.get("/api/v1/notifications/")
    get_response = client.get("/api/v1/notifications/1")

    assert appointment.id is not None
    assert list_response.status_code == 200
    assert list_response.json() == []
    assert get_response.status_code == 403


def test_admin_can_view_all_notifications(client, db):
    barber = make_user(db, email="notif-admin-view@test.com")
    create_valid_appointment(db, barber)

    response = client.get("/api/v1/notifications/")

    assert response.status_code == 200
    assert len(response.json()) >= 1
