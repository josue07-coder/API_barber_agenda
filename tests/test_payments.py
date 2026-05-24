from datetime import date, timedelta, time
from itertools import count

from app.api.deps import get_current_user
from app.main import app


PHONE_COUNTER = count(8090000000)


def future_date():
    return date.today() + timedelta(days=3)


def make_user(db, *, role="barber", email="payment-barber@test.com", is_active=True):
    from app.models.user import User

    user = User(
        name=email.split("@")[0],
        email=email,
        password="x",
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    return user


def make_client_and_service(db, *, price=100):
    from app.models.client import Client
    from app.models.service import Service

    client = Client(name="Cliente Pago", phone=str(next(PHONE_COUNTER)), is_active=True)
    service = Service(name="Corte Pago", duration_minutes=30, price=price, is_active=True)
    db.add_all([client, service])
    db.commit()
    return client, service


def add_schedule(db, barber, appointment_date):
    from app.models.barber_schedule import BarberSchedule

    db.add(
        BarberSchedule(
            barber_id=barber.id,
            weekday=appointment_date.weekday(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )
    )
    db.commit()


def create_appointment(db, barber, *, price=100, appointment_date=None, start_time=time(10, 0)):
    from app.schema.appointment import AppointmentCreate
    from app.services.appointment_service import create_new_appointment

    appointment_date = appointment_date or future_date()
    client_model, service = make_client_and_service(db, price=price)
    add_schedule(db, barber, appointment_date)
    appointment = create_new_appointment(
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
    return appointment, client_model, service


def payment_payload(appointment_id, amount="50.00", status="paid"):
    return {
        "appointment_id": appointment_id,
        "amount": amount,
        "currency": "DOP",
        "payment_method": "cash",
        "status": status,
        "transaction_reference": "RCPT-TEST",
        "notes": "Deposito",
    }


def test_create_valid_payment(client, db):
    barber = make_user(db, email="payment-valid@test.com")
    appointment, _, _ = create_appointment(db, barber)

    response = client.post("/api/v1/payments/", json=payment_payload(appointment.id))

    assert response.status_code == 200
    data = response.json()
    assert data["appointment_id"] == appointment.id
    assert data["client_id"] == appointment.client_id
    assert data["status"] == "paid"
    assert data["paid_at"] is not None


def test_reject_amount_less_or_equal_zero(client, db):
    barber = make_user(db, email="payment-zero@test.com")
    appointment, _, _ = create_appointment(db, barber)

    response = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="0"))

    assert response.status_code == 422


def test_reject_payment_on_cancelled_appointment(client, db):
    barber = make_user(db, email="payment-cancelled@test.com")
    appointment, _, _ = create_appointment(db, barber)
    appointment.status = "cancelada"
    db.commit()

    response = client.post("/api/v1/payments/", json=payment_payload(appointment.id))

    assert response.status_code == 400


def test_partial_payment_marks_appointment_partially_paid(client, db):
    barber = make_user(db, email="payment-partial@test.com")
    appointment, _, _ = create_appointment(db, barber, price=100)

    response = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="40.00"))

    assert response.status_code == 200
    db.refresh(appointment)
    assert appointment.payment_status == "partially_paid"


def test_full_payment_marks_appointment_paid(client, db):
    barber = make_user(db, email="payment-full@test.com")
    appointment, _, _ = create_appointment(db, barber, price=100)

    response = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="100.00"))

    assert response.status_code == 200
    db.refresh(appointment)
    assert appointment.payment_status == "paid"


def test_multiple_payments_can_complete_appointment_payment(client, db):
    barber = make_user(db, email="payment-multiple@test.com")
    appointment, _, _ = create_appointment(db, barber, price=100)

    first = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="30.00"))
    second = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="70.00"))
    list_response = client.get(f"/api/v1/payments/appointment/{appointment.id}")

    assert first.status_code == 200
    assert second.status_code == 200
    assert list_response.status_code == 200
    assert len(list_response.json()) == 2
    db.refresh(appointment)
    assert appointment.payment_status == "paid"


def test_refund_payment(client, db):
    barber = make_user(db, email="payment-refund@test.com")
    appointment, _, _ = create_appointment(db, barber, price=100)
    payment = client.post("/api/v1/payments/", json=payment_payload(appointment.id, amount="100.00")).json()

    response = client.patch(
        f"/api/v1/payments/{payment['id']}/refund",
        json={"reason": "Cliente solicito reembolso"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "refunded"
    db.refresh(appointment)
    assert appointment.payment_status == "refunded"


def test_mark_pending_payment_as_paid(client, db):
    barber = make_user(db, email="payment-mark-paid@test.com")
    appointment, _, _ = create_appointment(db, barber, price=100)
    payment = client.post(
        "/api/v1/payments/",
        json=payment_payload(appointment.id, amount="100.00", status="pending"),
    ).json()

    response = client.patch(
        f"/api/v1/payments/{payment['id']}/mark-paid",
        json={"transaction_reference": "AUTH-PAID", "notes": "Pago confirmado"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "paid"
    db.refresh(appointment)
    assert appointment.payment_status == "paid"


def test_barber_cannot_view_payment_from_other_barber(client, db):
    owner = make_user(db, email="payment-owner@test.com")
    other = make_user(db, email="payment-other@test.com")
    appointment, _, _ = create_appointment(db, owner)
    payment = client.post("/api/v1/payments/", json=payment_payload(appointment.id)).json()

    def override_other_barber():
        return other

    app.dependency_overrides[get_current_user] = override_other_barber

    response = client.get(f"/api/v1/payments/{payment['id']}")

    assert response.status_code == 403


def test_admin_can_view_payment(client, db):
    barber = make_user(db, email="payment-admin-view@test.com")
    appointment, _, _ = create_appointment(db, barber)
    payment = client.post("/api/v1/payments/", json=payment_payload(appointment.id)).json()

    response = client.get(f"/api/v1/payments/{payment['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == payment["id"]


def test_payment_summary(client, db):
    barber = make_user(db, email="payment-summary@test.com")
    appointment_one, _, _ = create_appointment(db, barber, price=100, start_time=time(10, 0))
    appointment_two, _, _ = create_appointment(db, barber, price=100, start_time=time(11, 0))
    client.post("/api/v1/payments/", json=payment_payload(appointment_one.id, amount="25.00"))
    client.post("/api/v1/payments/", json=payment_payload(appointment_two.id, amount="75.00"))

    response = client.get("/api/v1/payments/summary")

    assert response.status_code == 200
    data = response.json()
    assert data["total_payments"] == 2
    assert data["total_paid"] == 100.0
