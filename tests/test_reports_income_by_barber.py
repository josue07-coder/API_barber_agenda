def test_income_by_barber(db, client, admin_token):
    from datetime import date, time
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.models.appointment import Appointment
    from app.core.security import get_password_hash

    barber1 = User(
        name="Carlos",
        email="c@b.com",
        password=get_password_hash("123"),
        role="barber",
        is_active=True
    )
    barber2 = User(
        name="Luis",
        email="l@b.com",
        password=get_password_hash("123"),
        role="barber",
        is_active=True
    )
    client1 = Client(name="Ana", phone="111", is_active=True)

    service1 = Service(name="Corte", duration_minutes=30, price=100, is_active=True)
    service2 = Service(name="Barba", duration_minutes=20, price=50, is_active=True)

    db.add_all([barber1, barber2, client1, service1, service2])
    db.commit()

    a1 = Appointment(
        user_id=barber1.id,
        client_id=client1.id,
        service_id=service1.id,
        date=date.today(),
        start_time=time(10, 0),
        end_time=time(10, 30),
        status="completada"
    )
    a2 = Appointment(
        user_id=barber1.id,
        client_id=client1.id,
        service_id=service2.id,
        date=date.today(),
        start_time=time(11, 0),
        end_time=time(11, 20),
        status="completada"
    )
    a3 = Appointment(
        user_id=barber2.id,
        client_id=client1.id,
        service_id=service1.id,
        date=date.today(),
        start_time=time(12, 0),
        end_time=time(12, 30),
        status="completada"
    )

    db.add_all([a1, a2, a3])
    db.commit()

    response = client.get(
        f"/api/v1/reports/financial/by-barber"
        f"?start_date={date.today()}&end_date={date.today()}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data[0]["barber"] == "Carlos"
    assert data[0]["ingresos"] == 150