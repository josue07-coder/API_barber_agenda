from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.appointment import Appointment
from app.models.service import Service
from app.models.user import User
from app.models.client import Client

def count_appointment_by_status(db: Session, start_date, end_date):
        return(
                db.query(Appointment.status, func.count(Appointment.id))
                .filter(Appointment.date.between(start_date, end_date))
                .group_by(Appointment.status).all()
        )

def total_income(db: Session, start_date, end_date):
        return(
                db.query(func.sum(Service.price))
                .join(Appointment, Appointment.service_id == Service.id)
                .filter(
                        Appointment.status == "completada",
                        Appointment.date.between(start_date, end_date)
                ).scalar()

        )

def income_by_barber(db, start_date, end_date):
        return (
        db.query(
            User.id.label("barber_id"),
            User.name.label("barber"),
            func.coalesce(func.sum(Service.price), 0).label("ingresos")
        )
        .join(Appointment, Appointment.user_id == User.id)
        .join(Service, Appointment.service_id == Service.id)
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date),
            User.role == "barber"
        )
        .group_by(User.id, User.name)
        .order_by(func.sum(Service.price).desc())
        .all()  #  lista de filas (no Query)
    )

def income_by_service(db, start_date, end_date):
            return (
        db.query(
            Service.id.label("service_id"),
            Service.name.label("service"),
            func.coalesce(func.sum(Service.price), 0).label("ingresos")
        )
        .join(Appointment, Appointment.service_id == Service.id)
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date)
        )
        .group_by(Service.id, Service.name)
        .order_by(func.sum(Service.price).desc())
        .all()
    )

def frequent_clients(db, start_date, end_date):
            return (
        db.query(
            Client.id.label("client_id"),
            Client.name.label("client"),
            func.count(Appointment.id).label("visitas")
        )
        .join(Appointment, Appointment.client_id == Client.id)
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date)
        )
        .group_by(Client.id, Client.name)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )

def clients_with_no_show(db, start_date, end_date):
            return (
        db.query(
            Client.id.label("client_id"),
            Client.name.label("client"),
            func.count(Appointment.id).label("no_show")
        )
        .join(Appointment, Appointment.client_id == Client.id)
        .filter(
            Appointment.status == "no_show",
            Appointment.date.between(start_date, end_date)
        )
        .group_by(Client.id, Client.name)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )

def demand_by_hour(db, start_date, end_date):
            return (
        db.query(
            func.strftime("%H:00", Appointment.start_time).label("hour"),
            func.count(Appointment.id).label("total")
        )
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date)
        )
        .group_by("hour")
        .order_by(func.count(Appointment.id).desc())
        .all()
    )


def demand_by_weekday(db, start_date, end_date):
    return (
        db.query(
            func.strftime("%w", Appointment.date).label("weekday"),
            func.count(Appointment.id).label("total")
        )
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date)
        )
        .group_by("weekday")
        .order_by(func.count(Appointment.id).desc())
        .all()
    )