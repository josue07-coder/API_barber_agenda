def test_demand_by_hour_and_day(db, client, admin_token):
    from datetime import date, time
    from app.models.user import User
    from app.models.client import Client
    from app.models.service import Service
    from app.models.appointment import Appointment
    from app.core.security import get_password_hash

    barber = User(
        name="Carlos",
        email="c@b.com",
        password=get_password_hash("123"),
        role="barber",
        is_active=True
    )
    client1 = Client(name="Ana", phone="111", is_active=True)
    service = Service(name="Corte", duration_minutes=30, price=100, is_active=True)

    db.add_all([barber, client1, service])
    db.commit()

    a1 = Appointment(
        user_id=barber.id, client_id=client1.id, service_id=service.id,
        date=date.today(), start_time=time(10, 0), end_time=time(10, 30),
        status="completada"
    )
    a2 = Appointment(
        user_id=barber.id, client_id=client1.id, service_id=service.id,
        date=date.today(), start_time=time(10, 0), end_time=time(10, 30),
        status="completada"
    )
    a3 = Appointment(
        user_id=barber.id, client_id=client1.id, service_id=service.id,
        date=date.today(), start_time=time(11, 0), end_time=time(11, 30),
        status="completada"
    )

    db.add_all([a1, a2, a3])
    db.commit()

    r1 = client.get(
        f"/api/v1/reports/operations/hours"
        f"?start_date={date.today()}&end_date={date.today()}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r1.status_code == 200
    hours = r1.json()
    assert hours[0]["hour"] == "10:00"
    assert hours[0]["total"] == 2

    r2 = client.get(
        f"/api/v1/reports/operations/days"
        f"?start_date={date.today()}&end_date={date.today()}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert r2.status_code == 200
    days = r2.json()
    assert days[0]["total"] >= 1
