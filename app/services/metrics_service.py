from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.appointment import Appointment
from app.models.service import Service

from app.repositories.metrics_repo import (
        count_appointment_by_status,
        total_income, income_by_barber,
        income_by_service,
        frequent_clients,
        clients_with_no_show,
        demand_by_hour, demand_by_weekday
        
)

def get_dashboard_metrics(db: Session, start_date, end_date):
        status_counts = count_appointment_by_status(db, start_date, end_date)
        income = total_income(db, start_date, end_date) or 0

        metrics = {
                "total": 0,
                "agendadas": 0,
                "confirmada": 0,
                "completadas": 0,
                "canceladas": 0,
                "no_show": 0,
                "ingresos": income,
                "no_show_rate": 0
        }

        for status, count in status_counts:
                metrics["total"] += count
                metrics[status] = count

        if metrics["total"] > 0:
                metrics["no_show_rate"] = round(
                        (metrics["no_show"] / metrics["total"]) * 100, 2
                )

        return metrics

def get_income_by_barber(db, start_date, end_date):
        rows = income_by_barber(db, start_date, end_date)

        return [
           {
            "barber_id": r.barber_id,
            "barber": r.barber,
            "ingresos": float(r.ingresos)
           }
           for r in rows
        ]

def get_income_by_service(db, start_date, end_date):
        rows = income_by_service(db, start_date, end_date)

        return [
           {
            "service_id": r.service_id,
            "service": r.service,
            "ingresos": float(r.ingresos)
           }
           for r in rows
        ]

def get_frequent_clients(db, start_date, end_date):
        rows = frequent_clients(db, start_date, end_date)

        return [
        {
            "client_id": r.client_id,
            "client": r.client,
            "visitas": r.visitas
        }
        for r in rows
    ]

def get_clients_with_no_show(db, start_date, end_date):
        rows = clients_with_no_show(db, start_date, end_date)

        return [
        {
            "client_id": r.client_id,
            "client": r.client,
            "no_show": r.no_show
        }
        for r in rows
    ]

WEEKDAYS = {
    "0": "Sunday",
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
}


def get_demand_by_hour(db, start_date, end_date):
    rows = demand_by_hour(db, start_date, end_date)
    return [
        {"hour": r.hour, "total": r.total}
        for r in rows
    ]


def get_demand_by_weekday(db, start_date, end_date):
    rows = demand_by_weekday(db, start_date, end_date)
    return [
        {"weekday": WEEKDAYS.get(r.weekday, r.weekday), "total": r.total}
        for r in rows
    ]