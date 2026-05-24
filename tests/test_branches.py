from datetime import date, timedelta, time

from app.api.deps import get_current_user
from app.main import app


def future_date():
    return date.today() + timedelta(days=5)


def make_branch(db, name="Sucursal Test"):
    from app.models.branch import Branch

    branch = Branch(name=name, address="Calle 1", phone="8094440000", is_active=True)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_barber(db, branch=None, email="branch-barber@test.com"):
    from app.models.user import User

    barber = User(
        name="Branch Barber",
        email=email,
        password="x",
        role="barber",
        branch_id=branch.id if branch else None,
        is_active=True,
    )
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber


def make_client(db, phone="8094441000"):
    from app.models.client import Client

    client_model = Client(name="Branch Client", phone=phone, is_active=True)
    db.add(client_model)
    db.commit()
    db.refresh(client_model)
    return client_model


def add_schedule(db, barber, target_date):
    from app.models.barber_schedule import BarberSchedule

    db.add(
        BarberSchedule(
            barber_id=barber.id,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            is_active=True,
        )
    )
    db.commit()


def test_admin_creates_and_lists_branch(client):
    response = client.post(
        "/api/v1/branches/",
        json={
            "name": "Sucursal Centro",
            "address": "Av. Principal",
            "phone": "8094442000",
        },
    )
    list_response = client.get("/api/v1/branches/")

    assert response.status_code == 200
    assert response.json()["name"] == "Sucursal Centro"
    assert list_response.status_code == 200
    assert any(item["name"] == "Sucursal Centro" for item in list_response.json())


def test_barber_and_client_cannot_create_branch(client, db):
    barber = make_barber(db, email="branch-no-admin@test.com")

    def override_barber():
        return barber

    app.dependency_overrides[get_current_user] = override_barber
    response = client.post("/api/v1/branches/", json={"name": "No Admin"})

    assert response.status_code == 403


def test_admin_assigns_barber_to_branch(client, db):
    branch = make_branch(db, "Sucursal Asignacion")
    barber = make_barber(db, email="branch-assign@test.com")

    response = client.put(
        f"/api/v1/users/{barber.id}",
        json={"branch_id": branch.id},
    )

    assert response.status_code == 200
    assert response.json()["branch_id"] == branch.id


def test_service_can_be_assigned_to_branch(client, db):
    branch = make_branch(db, "Sucursal Servicios")

    response = client.post(
        "/api/v1/services/",
        json={
            "name": "Corte Sucursal",
            "duration_minutes": 30,
            "price": "500.00",
            "branch_id": branch.id,
        },
    )
    list_response = client.get(f"/api/v1/services/?branch_id={branch.id}")

    assert response.status_code == 200
    assert response.json()["branch_id"] == branch.id
    assert len(list_response.json()) == 1


def test_appointment_created_with_branch(client, db):
    from app.models.service import Service

    branch = make_branch(db, "Sucursal Citas")
    barber = make_barber(db, branch, "branch-appointment@test.com")
    client_model = make_client(db, "8094441001")
    target_date = future_date()
    add_schedule(db, barber, target_date)
    service = Service(
        name="Servicio Cita Sucursal",
        duration_minutes=30,
        price=100,
        branch_id=branch.id,
        is_active=True,
    )
    db.add(service)
    db.commit()

    response = client.post(
        "/api/v1/appointments/",
        json={
            "barber_id": barber.id,
            "client_id": client_model.id,
            "service_id": service.id,
            "date": target_date.isoformat(),
            "start_time": "10:00:00",
            "branch_id": branch.id,
        },
    )

    assert response.status_code == 200
    assert response.json()["branch_id"] == branch.id


def test_appointment_rejects_mismatched_branch(client, db):
    from app.models.service import Service

    branch_one = make_branch(db, "Sucursal Uno")
    branch_two = make_branch(db, "Sucursal Dos")
    barber = make_barber(db, branch_one, "branch-mismatch@test.com")
    client_model = make_client(db, "8094441002")
    target_date = future_date()
    add_schedule(db, barber, target_date)
    service = Service(
        name="Servicio Otra Sucursal",
        duration_minutes=30,
        price=100,
        branch_id=branch_two.id,
        is_active=True,
    )
    db.add(service)
    db.commit()

    response = client.post(
        "/api/v1/appointments/",
        json={
            "barber_id": barber.id,
            "client_id": client_model.id,
            "service_id": service.id,
            "date": target_date.isoformat(),
            "start_time": "10:00:00",
            "branch_id": branch_one.id,
        },
    )

    assert response.status_code == 400


def test_available_slots_filters_by_branch(client, db):
    from app.models.service import Service

    branch = make_branch(db, "Sucursal Disponibilidad")
    barber = make_barber(db, branch, "branch-slots@test.com")
    target_date = future_date()
    add_schedule(db, barber, target_date)
    service = Service(
        name="Servicio Slots",
        duration_minutes=30,
        price=100,
        branch_id=branch.id,
        is_active=True,
    )
    db.add(service)
    db.commit()

    response = client.get(
        "/api/v1/appointments/available-slots"
        f"?barber_id={barber.id}&service_id={service.id}"
        f"&date={target_date.isoformat()}&branch_id={branch.id}"
    )

    assert response.status_code == 200
    assert "10:00:00" in response.json()["slots"]


def test_income_by_branch_report(client, db):
    from app.models.appointment import Appointment
    from app.models.payment import Payment
    from app.models.service import Service
    from datetime import datetime, timezone

    branch = make_branch(db, "Sucursal Reporte")
    barber = make_barber(db, branch, "branch-report@test.com")
    client_model = make_client(db, "8094441003")
    service = Service(
        name="Servicio Reporte",
        duration_minutes=30,
        price=100,
        branch_id=branch.id,
        is_active=True,
    )
    db.add(service)
    db.commit()
    appointment = Appointment(
        user_id=barber.id,
        client_id=client_model.id,
        service_id=service.id,
        branch_id=branch.id,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status="completada",
    )
    db.add(appointment)
    db.commit()
    db.add(
        Payment(
            appointment_id=appointment.id,
            client_id=client_model.id,
            amount=75,
            currency="DOP",
            payment_method="cash",
            status="paid",
            paid_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    response = client.get(
        f"/api/v1/reports/financial/by-branch?start_date={date.today()}&end_date={date.today()}"
    )

    assert response.status_code == 200
    assert response.json()[0]["branch_id"] == branch.id
    assert response.json()[0]["ingresos"] == 75.0
