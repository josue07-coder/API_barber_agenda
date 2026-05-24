from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.metrics_repo import (
    clients_with_no_show,
    count_appointment_by_status,
    demand_by_hour,
    demand_by_weekday,
    frequent_clients,
    income_by_barber,
    income_by_day,
    income_by_month,
    income_by_payment_method,
    income_by_branch,
    income_by_service,
    payment_export_rows,
    pending_appointment_balances,
    total_income,
    total_refunded,
)


def money(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def validate_date_range(start_date, end_date):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Rango de fechas invalido")


def barber_filter_for_user(current_user: User) -> int | None:
    if current_user.role == "admin":
        return None
    if current_user.role == "barber":
        return current_user.id
    raise HTTPException(403, "No tienes permiso")


def get_dashboard_metrics(db: Session, start_date, end_date):
    status_counts = count_appointment_by_status(db, start_date, end_date)
    income = money(total_income(db, start_date, end_date))
    refunded = money(total_refunded(db, start_date, end_date))

    metrics = {
        "total": 0,
        "agendadas": 0,
        "confirmada": 0,
        "completadas": 0,
        "canceladas": 0,
        "no_show": 0,
        "ingresos": income,
        "total_reembolsado": refunded,
        "balance_neto": round(income - refunded, 2),
        "no_show_rate": 0,
    }

    for status, count in status_counts:
        metrics["total"] += count
        metrics[status] = count

    if metrics["total"] > 0:
        metrics["no_show_rate"] = round(
            (metrics["no_show"] / metrics["total"]) * 100, 2
        )

    return metrics


def get_income_by_barber(db, start_date, end_date, current_user: User | None = None):
    barber_id = None
    if current_user is not None:
        barber_id = barber_filter_for_user(current_user)

    rows = income_by_barber(db, start_date, end_date, barber_id=barber_id)

    return [
        {
            "barber_id": r.barber_id,
            "barber": r.barber,
            "ingresos": money(r.ingresos),
        }
        for r in rows
    ]


def get_income_by_service(db, start_date, end_date):
    rows = income_by_service(db, start_date, end_date)

    return [
        {
            "service_id": r.service_id,
            "service": r.service,
            "ingresos": money(r.ingresos),
        }
        for r in rows
    ]


def get_income_by_branch(db, start_date, end_date):
    rows = income_by_branch(db, start_date, end_date)

    return [
        {
            "branch_id": r.branch_id,
            "branch": r.branch,
            "ingresos": money(r.ingresos),
        }
        for r in rows
    ]


def get_income_by_payment_method(db, start_date, end_date):
    rows = income_by_payment_method(db, start_date, end_date)
    return [
        {
            "payment_method": r.payment_method,
            "payments": r.payments,
            "ingresos": money(r.ingresos),
        }
        for r in rows
    ]


def combine_period_rows(paid_rows, refunded_rows, period_builder):
    periods = {}
    for row in paid_rows:
        period = period_builder(row)
        periods.setdefault(period, {"period": period, "ingresos": 0.0, "reembolsos": 0.0})
        periods[period]["ingresos"] = money(row.paid)

    for row in refunded_rows:
        period = period_builder(row)
        periods.setdefault(period, {"period": period, "ingresos": 0.0, "reembolsos": 0.0})
        periods[period]["reembolsos"] = money(row.refunded)

    result = []
    for period in sorted(periods):
        item = periods[period]
        item["balance_neto"] = round(item["ingresos"] - item["reembolsos"], 2)
        result.append(item)
    return result


def get_income_by_day(db, start_date, end_date):
    paid_rows, refunded_rows = income_by_day(db, start_date, end_date)
    return combine_period_rows(paid_rows, refunded_rows, lambda row: str(row.period))


def get_income_by_month(db, start_date, end_date):
    paid_rows, refunded_rows = income_by_month(db, start_date, end_date)
    return combine_period_rows(
        paid_rows,
        refunded_rows,
        lambda row: f"{int(row.year):04d}-{int(row.month):02d}",
    )


def get_pending_balances(db, start_date, end_date, current_user: User):
    barber_id = barber_filter_for_user(current_user)
    rows = pending_appointment_balances(db, start_date, end_date, barber_id=barber_id)
    return [
        {
            "appointment_id": r.appointment_id,
            "date": r.date.isoformat(),
            "client_id": r.client_id,
            "client": r.client,
            "barber_id": r.barber_id,
            "barber": r.barber,
            "service_id": r.service_id,
            "service": r.service,
            "service_price": money(r.service_price),
            "paid_amount": money(r.paid_amount),
            "pending_balance": money(r.pending_balance),
            "payment_status": r.payment_status,
        }
        for r in rows
    ]


def get_payment_export_data(db, start_date, end_date, current_user: User):
    barber_id = barber_filter_for_user(current_user)
    rows = payment_export_rows(db, start_date, end_date, barber_id=barber_id)
    data = []

    for payment, appointment, client, barber, service in rows:
        paid_amount = payment.amount if payment.status in {"paid", "partially_paid"} else 0
        refunded_amount = payment.amount if payment.status == "refunded" else 0
        balance = money(paid_amount) - money(refunded_amount)
        data.append(
            {
                "fecha": appointment.date.isoformat(),
                "cita": appointment.id,
                "cliente": client.name,
                "barbero": barber.name,
                "servicio": service.name,
                "metodo_pago": payment.payment_method,
                "monto_pagado": money(paid_amount),
                "monto_reembolsado": money(refunded_amount),
                "balance_neto": round(balance, 2),
                "estado_pago": payment.status,
            }
        )

    return data


def get_frequent_clients(db, start_date, end_date):
    rows = frequent_clients(db, start_date, end_date)

    return [
        {
            "client_id": r.client_id,
            "client": r.client,
            "visitas": r.visitas,
        }
        for r in rows
    ]


def get_clients_with_no_show(db, start_date, end_date):
    rows = clients_with_no_show(db, start_date, end_date)

    return [
        {
            "client_id": r.client_id,
            "client": r.client,
            "no_show": r.no_show,
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
        {"weekday": WEEKDAYS.get(str(int(r.weekday)), str(r.weekday)), "total": r.total}
        for r in rows
    ]
