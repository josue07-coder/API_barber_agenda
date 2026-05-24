from datetime import date
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import dashboard_repo as repo


def money(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def pct(part: int | float, total: int | float) -> float:
    return round((float(part) / float(total)) * 100, 2) if total else 0.0


def rows_to_items(rows):
    return [{"label": str(row.label), "value": money(row.value)} for row in rows]


def rows_to_named_items(rows):
    return [{"id": row.id, "label": row.label, "value": money(row.value)} for row in rows]


def normalize_filters(
    current_user: User,
    start_date: date,
    end_date: date,
    branch_id: int | None,
    barber_id: int | None,
) -> tuple[int | None, int | None]:
    if start_date > end_date:
        raise HTTPException(400, "Rango de fechas invalido")

    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso para acceder al dashboard")

    if current_user.role == "barber":
        if barber_id is not None and barber_id != current_user.id:
            raise HTTPException(403, "No puedes consultar metricas de otro barbero")
        if branch_id is not None and current_user.branch_id is not None and branch_id != current_user.branch_id:
            raise HTTPException(403, "No puedes consultar otra sucursal")
        return current_user.branch_id, current_user.id

    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")

    return branch_id, barber_id


def today_upcoming_payload(appointments):
    return [
        {
            "id": appointment.id,
            "date": appointment.date.isoformat(),
            "start_time": appointment.start_time.isoformat(),
            "status": appointment.status,
            "client_id": appointment.client_id,
            "barber_id": appointment.user_id,
            "service_id": appointment.service_id,
            "branch_id": appointment.branch_id,
        }
        for appointment in appointments
    ]


def scoped(db, current_user, start_date, end_date, branch_id, barber_id):
    branch_id, barber_id = normalize_filters(current_user, start_date, end_date, branch_id, barber_id)
    return branch_id, barber_id


def overview(db: Session, current_user: User, start_date: date, end_date: date, branch_id=None, barber_id=None):
    branch_id, barber_id = scoped(db, current_user, start_date, end_date, branch_id, barber_id)
    total = repo.appointment_total(db, start_date, end_date, branch_id, barber_id)
    completed = repo.appointment_total(db, start_date, end_date, branch_id, barber_id, "completada")
    cancelled = repo.appointment_total(db, start_date, end_date, branch_id, barber_id, "cancelada")
    no_show = repo.appointment_total(db, start_date, end_date, branch_id, barber_id, "no_show")
    revenue = money(repo.revenue_total(db, start_date, end_date, branch_id, barber_id))
    refunds = money(repo.refund_total(db, start_date, end_date, branch_id, barber_id))
    return {
        "totals": {
            "total_appointments": total,
            "completed_appointments": completed,
            "cancelled_appointments": cancelled,
            "no_show_appointments": no_show,
            "total_revenue": revenue,
            "total_refunds": refunds,
            "net_revenue": round(revenue - refunds, 2),
            "pending_payments": repo.pending_payment_total(db, start_date, end_date, branch_id, barber_id),
            "active_clients": repo.active_clients_count(db),
            "new_clients": repo.new_clients_count(db, start_date, end_date, branch_id, barber_id),
        },
        "top_services": rows_to_named_items(repo.top_services(db, start_date, end_date, branch_id, barber_id)),
        "top_barbers": rows_to_named_items(repo.top_barbers(db, start_date, end_date, branch_id, barber_id)),
        "upcoming_appointments_today": today_upcoming_payload(repo.upcoming_today(db, date.today(), branch_id, barber_id)),
    }


def financial(db: Session, current_user: User, start_date: date, end_date: date, branch_id=None, barber_id=None):
    branch_id, barber_id = scoped(db, current_user, start_date, end_date, branch_id, barber_id)
    methods = {row.label: money(row.value) for row in repo.revenue_by_payment_method(db, start_date, end_date, branch_id, barber_id)}
    revenue = money(repo.revenue_total(db, start_date, end_date, branch_id, barber_id))
    refunds = money(repo.refund_total(db, start_date, end_date, branch_id, barber_id))
    commissions = {row.label: money(row.value) for row in repo.commission_totals(db, start_date, end_date, branch_id, barber_id)}
    return {
        "revenue_by_day": rows_to_items(repo.revenue_by_day(db, start_date, end_date, branch_id, barber_id)),
        "revenue_by_month": [
            {"label": f"{int(row.year):04d}-{int(row.month):02d}", "value": money(row.value)}
            for row in repo.revenue_by_month(db, start_date, end_date, branch_id, barber_id)
        ],
        "revenue_by_payment_method": [{"label": key, "value": value} for key, value in methods.items()],
        "revenue_by_branch": rows_to_named_items(repo.revenue_by_branch(db, start_date, end_date, branch_id, barber_id)),
        "revenue_by_barber": rows_to_named_items(repo.revenue_by_barber(db, start_date, end_date, branch_id, barber_id)),
        "cash_income": methods.get("cash", 0.0),
        "card_income": methods.get("card", 0.0),
        "transfer_income": methods.get("transfer", 0.0),
        "online_income": methods.get("online", 0.0),
        "refunds": refunds,
        "net_revenue": round(revenue - refunds, 2),
        "pending_balances": repo.pending_balances_count(db, start_date, end_date, branch_id, barber_id),
        "commissions_pending": commissions.get("pending", 0.0),
        "commissions_paid": commissions.get("paid", 0.0),
    }


def appointments(db: Session, current_user: User, start_date: date, end_date: date, branch_id=None, barber_id=None):
    branch_id, barber_id = scoped(db, current_user, start_date, end_date, branch_id, barber_id)
    total = repo.appointment_total(db, start_date, end_date, branch_id, barber_id)
    cancelled = repo.appointment_total(db, start_date, end_date, branch_id, barber_id, "cancelada")
    no_show = repo.appointment_total(db, start_date, end_date, branch_id, barber_id, "no_show")
    days = max((end_date - start_date).days + 1, 1)
    return {
        "appointments_by_status": rows_to_items(repo.appointment_status_counts(db, start_date, end_date, branch_id, barber_id)),
        "appointments_by_day": rows_to_items(repo.appointments_by_day(db, start_date, end_date, branch_id, barber_id)),
        "appointments_by_hour": rows_to_items(repo.appointments_by_hour(db, start_date, end_date, branch_id, barber_id)),
        "cancellation_rate": pct(cancelled, total),
        "no_show_rate": pct(no_show, total),
        "average_appointments_per_day": round(total / days, 2),
        "upcoming_appointments": today_upcoming_payload(repo.upcoming_today(db, date.today(), branch_id, barber_id)),
        "busiest_hours": rows_to_items(repo.appointments_by_hour(db, start_date, end_date, branch_id, barber_id)),
        "busiest_days": rows_to_items(repo.appointments_by_weekday(db, start_date, end_date, branch_id, barber_id)),
    }


def barbers(db: Session, current_user: User, start_date: date, end_date: date, branch_id=None, barber_id=None):
    branch_id, barber_id = scoped(db, current_user, start_date, end_date, branch_id, barber_id)
    revenue = {row.id: money(row.value) for row in repo.revenue_by_barber(db, start_date, end_date, branch_id, barber_id)}
    commissions = {row.barber_id: money(row.value) for row in repo.commissions_by_barber(db, start_date, end_date, branch_id, barber_id)}
    performance = []
    for row in repo.barber_performance(db, start_date, end_date, branch_id, barber_id):
        performance.append(
            {
                "barber_id": row.barber_id,
                "barber": row.barber,
                "appointments": row.appointments,
                "revenue": revenue.get(row.barber_id, 0.0),
                "commissions": commissions.get(row.barber_id, 0.0),
                "completion_rate": pct(row.completed, row.appointments),
                "cancellation_rate": pct(row.cancelled, row.appointments),
                "no_show_rate": pct(row.no_show, row.appointments),
            }
        )
    return {
        "appointments_per_barber": [{"barber_id": item["barber_id"], "label": item["barber"], "value": item["appointments"]} for item in performance],
        "revenue_per_barber": [{"barber_id": item["barber_id"], "label": item["barber"], "value": item["revenue"]} for item in performance],
        "commissions_per_barber": [{"barber_id": item["barber_id"], "label": item["barber"], "value": item["commissions"]} for item in performance],
        "completion_rate_per_barber": [{"barber_id": item["barber_id"], "label": item["barber"], "value": item["completion_rate"]} for item in performance],
        "cancellation_rate_per_barber": [{"barber_id": item["barber_id"], "label": item["barber"], "value": item["cancellation_rate"]} for item in performance],
        "no_show_rate_per_barber": [{"barber_id": item["barber_id"], "label": item["barber"], "value": item["no_show_rate"]} for item in performance],
    }


def clients(db: Session, current_user: User, start_date: date, end_date: date, branch_id=None, barber_id=None):
    branch_id, barber_id = scoped(db, current_user, start_date, end_date, branch_id, barber_id)
    return {
        "new_clients_by_day": rows_to_items(repo.new_clients_by_day(db, start_date, end_date, branch_id, barber_id)),
        "top_clients_by_visits": rows_to_named_items(repo.client_visits(db, start_date, end_date, branch_id, barber_id)),
        "top_clients_by_revenue": rows_to_named_items(repo.client_revenue(db, start_date, end_date, branch_id, barber_id)),
        "clients_with_pending_balances": repo.pending_balances_count(db, start_date, end_date, branch_id, barber_id),
        "clients_with_no_show": repo.appointment_total(db, start_date, end_date, branch_id, barber_id, "no_show"),
        "active_clients": repo.active_clients_count(db),
        "inactive_clients": repo.inactive_clients_count(db),
    }


def branches(db: Session, current_user: User, start_date: date, end_date: date, branch_id=None, barber_id=None):
    branch_id, barber_id = scoped(db, current_user, start_date, end_date, branch_id, barber_id)
    revenue = {row.id: {"branch_id": row.id, "label": row.label, "revenue": money(row.value)} for row in repo.revenue_by_branch(db, start_date, end_date, branch_id, barber_id)}
    appointments_by_branch = {row.id: money(row.value) for row in repo.branch_appointments(db, start_date, end_date, branch_id, barber_id)}
    clients_by_branch = {row.branch_id: money(row.value) for row in repo.branch_clients(db, start_date, end_date, branch_id, barber_id)}
    barbers_by_branch = {row.branch_id: money(row.value) for row in repo.branch_barbers(db, branch_id)}
    comparison = []
    for branch_data in revenue.values():
        bid = branch_data["branch_id"]
        comparison.append(
            {
                **branch_data,
                "appointments": appointments_by_branch.get(bid, 0),
                "clients": clients_by_branch.get(bid, 0),
                "barbers": barbers_by_branch.get(bid, 0),
            }
        )
    return {
        "revenue_per_branch": [{"branch_id": item["branch_id"], "label": item["label"], "value": item["revenue"]} for item in comparison],
        "appointments_per_branch": [{"branch_id": item["branch_id"], "label": item["label"], "value": item["appointments"]} for item in comparison],
        "clients_per_branch": [{"branch_id": item["branch_id"], "label": item["label"], "value": item["clients"]} for item in comparison],
        "barbers_per_branch": [{"branch_id": item["branch_id"], "label": item["label"], "value": item["barbers"]} for item in comparison],
        "cash_sessions_summary": [
            {
                "branch_id": row.branch_id,
                "status": row.status,
                "sessions": row.sessions,
                "expected": money(row.expected),
                "difference": money(row.difference),
            }
            for row in repo.cash_session_summary(db, start_date, end_date, branch_id)
        ],
        "branch_comparison": comparison,
    }
