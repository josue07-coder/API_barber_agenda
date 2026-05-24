from sqlalchemy import case, extract, func
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.barber_commission import BarberCommission
from app.models.branch import Branch
from app.models.cash_movement import CashMovement
from app.models.cash_session import CashSession
from app.models.client import Client
from app.models.payment import Payment
from app.models.service import Service
from app.models.user import User


PAID_STATUSES = ("paid", "partially_paid")


def date_filter(column, start_date, end_date):
    return func.date(column).between(start_date, end_date)


def appointment_scope(query, start_date, end_date, branch_id=None, barber_id=None):
    query = query.filter(Appointment.date.between(start_date, end_date))
    if branch_id is not None:
        query = query.filter(Appointment.branch_id == branch_id)
    if barber_id is not None:
        query = query.filter(Appointment.user_id == barber_id)
    return query


def payment_scope(query, start_date, end_date, branch_id=None, barber_id=None, refunded=False):
    query = query.join(Appointment, Payment.appointment_id == Appointment.id)
    if refunded:
        query = query.filter(Payment.status == "refunded", Payment.refunded_at.isnot(None))
        query = query.filter(date_filter(Payment.refunded_at, start_date, end_date))
    else:
        query = query.filter(Payment.status.in_(PAID_STATUSES), Payment.paid_at.isnot(None))
        query = query.filter(date_filter(Payment.paid_at, start_date, end_date))
    if branch_id is not None:
        query = query.filter(Appointment.branch_id == branch_id)
    if barber_id is not None:
        query = query.filter(Appointment.user_id == barber_id)
    return query


def appointment_status_counts(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        appointment_scope(
            db.query(Appointment.status.label("label"), func.count(Appointment.id).label("value")),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .group_by(Appointment.status)
        .all()
    )


def appointment_total(db: Session, start_date, end_date, branch_id=None, barber_id=None, status=None):
    query = appointment_scope(db.query(func.count(Appointment.id)), start_date, end_date, branch_id, barber_id)
    if status is not None:
        query = query.filter(Appointment.status == status)
    return query.scalar() or 0


def revenue_total(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        payment_scope(db.query(func.coalesce(func.sum(Payment.amount), 0)), start_date, end_date, branch_id, barber_id)
        .scalar()
        or 0
    )


def refund_total(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        payment_scope(
            db.query(func.coalesce(func.sum(Payment.amount), 0)),
            start_date,
            end_date,
            branch_id,
            barber_id,
            refunded=True,
        )
        .scalar()
        or 0
    )


def pending_payment_total(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        appointment_scope(
            db.query(func.count(Appointment.id)),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .filter(Appointment.payment_status.in_(["pending", "partially_paid"]))
    )
    return query.scalar() or 0


def active_clients_count(db: Session):
    return db.query(func.count(Client.id)).filter(Client.is_active == True).scalar() or 0


def inactive_clients_count(db: Session):
    return db.query(func.count(Client.id)).filter(Client.is_active == False).scalar() or 0


def new_clients_count(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        db.query(func.count(func.distinct(Client.id)))
        .join(Appointment, Appointment.client_id == Client.id)
    )
    query = appointment_scope(query, start_date, end_date, branch_id, barber_id)
    return query.scalar() or 0


def top_services(db: Session, start_date, end_date, branch_id=None, barber_id=None, limit=5):
    query = (
        db.query(
            Service.id.label("id"),
            Service.name.label("label"),
            func.count(Appointment.id).label("value"),
        )
        .join(Appointment, Appointment.service_id == Service.id)
    )
    return (
        appointment_scope(query, start_date, end_date, branch_id, barber_id)
        .group_by(Service.id, Service.name)
        .order_by(func.count(Appointment.id).desc())
        .limit(limit)
        .all()
    )


def top_barbers(db: Session, start_date, end_date, branch_id=None, barber_id=None, limit=5):
    query = (
        db.query(
            User.id.label("id"),
            User.name.label("label"),
            func.count(Appointment.id).label("value"),
        )
        .join(Appointment, Appointment.user_id == User.id)
        .filter(User.role == "barber")
    )
    return (
        appointment_scope(query, start_date, end_date, branch_id, barber_id)
        .group_by(User.id, User.name)
        .order_by(func.count(Appointment.id).desc())
        .limit(limit)
        .all()
    )


def upcoming_today(db: Session, today, branch_id=None, barber_id=None, limit=10):
    query = db.query(Appointment).filter(
        Appointment.date == today,
        Appointment.status.in_(["agendada", "confirmada"]),
    )
    if branch_id is not None:
        query = query.filter(Appointment.branch_id == branch_id)
    if barber_id is not None:
        query = query.filter(Appointment.user_id == barber_id)
    return query.order_by(Appointment.start_time).limit(limit).all()


def revenue_by_day(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        payment_scope(
            db.query(
                func.date(Payment.paid_at).label("label"),
                func.coalesce(func.sum(Payment.amount), 0).label("value"),
            ),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .group_by("label")
        .order_by("label")
        .all()
    )


def revenue_by_month(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        payment_scope(
            db.query(
                extract("year", Payment.paid_at).label("year"),
                extract("month", Payment.paid_at).label("month"),
                func.coalesce(func.sum(Payment.amount), 0).label("value"),
            ),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )


def revenue_by_payment_method(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        payment_scope(
            db.query(Payment.payment_method.label("label"), func.coalesce(func.sum(Payment.amount), 0).label("value")),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .group_by(Payment.payment_method)
        .all()
    )


def revenue_by_branch(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        db.query(Branch.id.label("id"), Branch.name.label("label"), func.coalesce(func.sum(Payment.amount), 0).label("value"))
        .join(Appointment, Appointment.branch_id == Branch.id)
        .join(Payment, Payment.appointment_id == Appointment.id)
        .filter(Payment.status.in_(PAID_STATUSES), Payment.paid_at.isnot(None))
        .filter(date_filter(Payment.paid_at, start_date, end_date))
    )
    return (
        query
        .filter(Branch.id == branch_id if branch_id is not None else True)
        .filter(Appointment.user_id == barber_id if barber_id is not None else True)
        .group_by(Branch.id, Branch.name)
        .all()
    )


def revenue_by_barber(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        db.query(User.id.label("id"), User.name.label("label"), func.coalesce(func.sum(Payment.amount), 0).label("value"))
        .join(Appointment, Appointment.user_id == User.id)
        .join(Payment, Payment.appointment_id == Appointment.id)
        .filter(User.role == "barber")
        .filter(Payment.status.in_(PAID_STATUSES), Payment.paid_at.isnot(None))
        .filter(date_filter(Payment.paid_at, start_date, end_date))
    )
    return (
        query
        .filter(Appointment.branch_id == branch_id if branch_id is not None else True)
        .filter(User.id == barber_id if barber_id is not None else True)
        .group_by(User.id, User.name)
        .all()
    )


def pending_balances_count(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return pending_payment_total(db, start_date, end_date, branch_id, barber_id)


def commission_totals(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = db.query(
        BarberCommission.status.label("label"),
        func.coalesce(func.sum(BarberCommission.commission_amount), 0).label("value"),
    ).filter(date_filter(BarberCommission.calculated_at, start_date, end_date))
    if branch_id is not None:
        query = query.filter(BarberCommission.branch_id == branch_id)
    if barber_id is not None:
        query = query.filter(BarberCommission.barber_id == barber_id)
    return query.group_by(BarberCommission.status).all()


def appointments_by_day(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        appointment_scope(
            db.query(Appointment.date.label("label"), func.count(Appointment.id).label("value")),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .group_by(Appointment.date)
        .order_by(Appointment.date)
        .all()
    )


def appointments_by_hour(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        appointment_scope(
            db.query(extract("hour", Appointment.start_time).label("label"), func.count(Appointment.id).label("value")),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .group_by("label")
        .order_by(func.count(Appointment.id).desc())
        .all()
    )


def appointments_by_weekday(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    return (
        appointment_scope(
            db.query(extract("dow", Appointment.date).label("label"), func.count(Appointment.id).label("value")),
            start_date,
            end_date,
            branch_id,
            barber_id,
        )
        .group_by("label")
        .order_by(func.count(Appointment.id).desc())
        .all()
    )


def barber_performance(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    total = func.count(Appointment.id)
    completed = func.coalesce(func.sum(case((Appointment.status == "completada", 1), else_=0)), 0)
    cancelled = func.coalesce(func.sum(case((Appointment.status == "cancelada", 1), else_=0)), 0)
    no_show = func.coalesce(func.sum(case((Appointment.status == "no_show", 1), else_=0)), 0)
    query = (
        db.query(
            User.id.label("barber_id"),
            User.name.label("barber"),
            total.label("appointments"),
            completed.label("completed"),
            cancelled.label("cancelled"),
            no_show.label("no_show"),
        )
        .join(Appointment, Appointment.user_id == User.id)
        .filter(User.role == "barber")
    )
    return (
        appointment_scope(query, start_date, end_date, branch_id, barber_id)
        .group_by(User.id, User.name)
        .all()
    )


def commissions_by_barber(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        db.query(
            BarberCommission.barber_id.label("barber_id"),
            func.coalesce(func.sum(BarberCommission.commission_amount), 0).label("value"),
        )
        .filter(BarberCommission.status != "cancelled")
        .filter(date_filter(BarberCommission.calculated_at, start_date, end_date))
    )
    if branch_id is not None:
        query = query.filter(BarberCommission.branch_id == branch_id)
    if barber_id is not None:
        query = query.filter(BarberCommission.barber_id == barber_id)
    return query.group_by(BarberCommission.barber_id).all()


def client_visits(db: Session, start_date, end_date, branch_id=None, barber_id=None, limit=10):
    query = (
        db.query(Client.id.label("id"), Client.name.label("label"), func.count(Appointment.id).label("value"))
        .join(Appointment, Appointment.client_id == Client.id)
    )
    return (
        appointment_scope(query, start_date, end_date, branch_id, barber_id)
        .group_by(Client.id, Client.name)
        .order_by(func.count(Appointment.id).desc())
        .limit(limit)
        .all()
    )


def client_revenue(db: Session, start_date, end_date, branch_id=None, barber_id=None, limit=10):
    query = (
        db.query(Client.id.label("id"), Client.name.label("label"), func.coalesce(func.sum(Payment.amount), 0).label("value"))
        .join(Appointment, Appointment.client_id == Client.id)
        .join(Payment, Payment.appointment_id == Appointment.id)
        .filter(Payment.status.in_(PAID_STATUSES), Payment.paid_at.isnot(None))
        .filter(date_filter(Payment.paid_at, start_date, end_date))
    )
    return (
        query
        .filter(Appointment.branch_id == branch_id if branch_id is not None else True)
        .filter(Appointment.user_id == barber_id if barber_id is not None else True)
        .group_by(Client.id, Client.name)
        .order_by(func.sum(Payment.amount).desc())
        .limit(limit)
        .all()
    )


def new_clients_by_day(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        db.query(Appointment.date.label("label"), func.count(func.distinct(Client.id)).label("value"))
        .join(Client, Appointment.client_id == Client.id)
    )
    return (
        appointment_scope(query, start_date, end_date, branch_id, barber_id)
        .group_by(Appointment.date)
        .order_by(Appointment.date)
        .all()
    )


def branch_appointments(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        db.query(Branch.id.label("id"), Branch.name.label("label"), func.count(Appointment.id).label("value"))
        .join(Appointment, Appointment.branch_id == Branch.id)
    )
    return (
        appointment_scope(query, start_date, end_date, branch_id, barber_id)
        .group_by(Branch.id, Branch.name)
        .all()
    )


def branch_barbers(db: Session, branch_id=None):
    query = db.query(User.branch_id.label("branch_id"), func.count(User.id).label("value")).filter(User.role == "barber")
    if branch_id is not None:
        query = query.filter(User.branch_id == branch_id)
    return query.group_by(User.branch_id).all()


def branch_clients(db: Session, start_date, end_date, branch_id=None, barber_id=None):
    query = (
        db.query(Appointment.branch_id.label("branch_id"), func.count(func.distinct(Appointment.client_id)).label("value"))
    )
    return (
        appointment_scope(query, start_date, end_date, branch_id, barber_id)
        .group_by(Appointment.branch_id)
        .all()
    )


def cash_session_summary(db: Session, start_date, end_date, branch_id=None):
    query = db.query(
        CashSession.branch_id.label("branch_id"),
        CashSession.status.label("status"),
        func.count(CashSession.id).label("sessions"),
        func.coalesce(func.sum(CashSession.expected_amount), 0).label("expected"),
        func.coalesce(func.sum(CashSession.difference_amount), 0).label("difference"),
    ).filter(date_filter(CashSession.opened_at, start_date, end_date))
    if branch_id is not None:
        query = query.filter(CashSession.branch_id == branch_id)
    return query.group_by(CashSession.branch_id, CashSession.status).all()


def cash_income_total(db: Session, start_date, end_date, branch_id=None):
    query = (
        db.query(func.coalesce(func.sum(CashMovement.amount), 0))
        .join(CashSession, CashMovement.cash_session_id == CashSession.id)
        .filter(CashMovement.movement_type == "income", CashMovement.method == "cash")
        .filter(date_filter(CashMovement.created_at, start_date, end_date))
    )
    if branch_id is not None:
        query = query.filter(CashSession.branch_id == branch_id)
    return query.scalar() or 0
