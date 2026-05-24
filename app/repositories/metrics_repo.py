from sqlalchemy import case, extract, func, or_
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.branch import Branch
from app.models.client import Client
from app.models.payment import Payment
from app.models.service import Service
from app.models.user import User


PAID_PAYMENT_STATUSES = ("paid", "partially_paid")


def db_dialect_name(db: Session) -> str:
    bind = db.get_bind()
    return bind.dialect.name


def hour_bucket_expression(dialect_name: str):
    if dialect_name == "postgresql":
        return func.to_char(Appointment.start_time, "HH24:00").label("hour")

    return func.strftime("%H:00", Appointment.start_time).label("hour")


def weekday_bucket_expression(dialect_name: str):
    if dialect_name == "postgresql":
        return extract("dow", Appointment.date).label("weekday")

    return func.strftime("%w", Appointment.date).label("weekday")


def _paid_date_filter(query, start_date, end_date):
    return query.filter(
        Payment.status.in_(PAID_PAYMENT_STATUSES),
        Payment.paid_at.isnot(None),
        func.date(Payment.paid_at).between(start_date, end_date),
    )


def _refunded_date_filter(query, start_date, end_date):
    return query.filter(
        Payment.status == "refunded",
        Payment.refunded_at.isnot(None),
        func.date(Payment.refunded_at).between(start_date, end_date),
    )


def count_appointment_by_status(db: Session, start_date, end_date):
    return (
        db.query(Appointment.status, func.count(Appointment.id))
        .filter(Appointment.date.between(start_date, end_date))
        .group_by(Appointment.status)
        .all()
    )


def total_income(db: Session, start_date, end_date):
    return _paid_date_filter(
        db.query(func.coalesce(func.sum(Payment.amount), 0)),
        start_date,
        end_date,
    ).scalar()


def total_refunded(db: Session, start_date, end_date):
    return _refunded_date_filter(
        db.query(func.coalesce(func.sum(Payment.amount), 0)),
        start_date,
        end_date,
    ).scalar()


def income_by_barber(db, start_date, end_date, barber_id=None):
    query = (
        db.query(
            User.id.label("barber_id"),
            User.name.label("barber"),
            func.coalesce(func.sum(Payment.amount), 0).label("ingresos"),
        )
        .join(Appointment, Appointment.user_id == User.id)
        .join(Payment, Payment.appointment_id == Appointment.id)
        .filter(User.role == "barber")
    )
    query = _paid_date_filter(query, start_date, end_date)

    if barber_id is not None:
        query = query.filter(User.id == barber_id)

    return (
        query.group_by(User.id, User.name)
        .order_by(func.sum(Payment.amount).desc())
        .all()
    )


def income_by_service(db, start_date, end_date):
    return (
        _paid_date_filter(
            db.query(
                Service.id.label("service_id"),
                Service.name.label("service"),
                func.coalesce(func.sum(Payment.amount), 0).label("ingresos"),
            )
            .join(Appointment, Appointment.service_id == Service.id)
            .join(Payment, Payment.appointment_id == Appointment.id),
            start_date,
            end_date,
        )
        .group_by(Service.id, Service.name)
        .order_by(func.sum(Payment.amount).desc())
        .all()
    )


def income_by_branch(db, start_date, end_date):
    return (
        _paid_date_filter(
            db.query(
                Branch.id.label("branch_id"),
                Branch.name.label("branch"),
                func.coalesce(func.sum(Payment.amount), 0).label("ingresos"),
            )
            .join(Appointment, Appointment.branch_id == Branch.id)
            .join(Payment, Payment.appointment_id == Appointment.id),
            start_date,
            end_date,
        )
        .group_by(Branch.id, Branch.name)
        .order_by(func.sum(Payment.amount).desc())
        .all()
    )


def income_by_payment_method(db, start_date, end_date):
    return (
        _paid_date_filter(
            db.query(
                Payment.payment_method.label("payment_method"),
                func.coalesce(func.sum(Payment.amount), 0).label("ingresos"),
                func.count(Payment.id).label("payments"),
            ),
            start_date,
            end_date,
        )
        .group_by(Payment.payment_method)
        .order_by(func.sum(Payment.amount).desc())
        .all()
    )


def income_by_day(db, start_date, end_date):
    paid_rows = (
        _paid_date_filter(
            db.query(
                func.date(Payment.paid_at).label("period"),
                func.coalesce(func.sum(Payment.amount), 0).label("paid"),
            ),
            start_date,
            end_date,
        )
        .group_by("period")
        .all()
    )
    refunded_rows = (
        _refunded_date_filter(
            db.query(
                func.date(Payment.refunded_at).label("period"),
                func.coalesce(func.sum(Payment.amount), 0).label("refunded"),
            ),
            start_date,
            end_date,
        )
        .group_by("period")
        .all()
    )
    return paid_rows, refunded_rows


def income_by_month(db, start_date, end_date):
    paid_rows = (
        _paid_date_filter(
            db.query(
                extract("year", Payment.paid_at).label("year"),
                extract("month", Payment.paid_at).label("month"),
                func.coalesce(func.sum(Payment.amount), 0).label("paid"),
            ),
            start_date,
            end_date,
        )
        .group_by("year", "month")
        .all()
    )
    refunded_rows = (
        _refunded_date_filter(
            db.query(
                extract("year", Payment.refunded_at).label("year"),
                extract("month", Payment.refunded_at).label("month"),
                func.coalesce(func.sum(Payment.amount), 0).label("refunded"),
            ),
            start_date,
            end_date,
        )
        .group_by("year", "month")
        .all()
    )
    return paid_rows, refunded_rows


def pending_appointment_balances(db, start_date, end_date, barber_id=None):
    paid_total = func.coalesce(
        func.sum(
            case(
                (Payment.status.in_(PAID_PAYMENT_STATUSES), Payment.amount),
                else_=0,
            )
        ),
        0,
    )
    query = (
        db.query(
            Appointment.id.label("appointment_id"),
            Appointment.date.label("date"),
            Client.id.label("client_id"),
            Client.name.label("client"),
            User.id.label("barber_id"),
            User.name.label("barber"),
            Service.id.label("service_id"),
            Service.name.label("service"),
            Service.price.label("service_price"),
            paid_total.label("paid_amount"),
            (Service.price - paid_total).label("pending_balance"),
            Appointment.payment_status.label("payment_status"),
        )
        .join(Client, Appointment.client_id == Client.id)
        .join(User, Appointment.user_id == User.id)
        .join(Service, Appointment.service_id == Service.id)
        .outerjoin(Payment, Payment.appointment_id == Appointment.id)
        .filter(Appointment.status != "cancelada")
        .filter(Appointment.date.between(start_date, end_date))
    )

    if barber_id is not None:
        query = query.filter(Appointment.user_id == barber_id)

    return (
        query.group_by(
            Appointment.id,
            Appointment.date,
            Client.id,
            Client.name,
            User.id,
            User.name,
            Service.id,
            Service.name,
            Service.price,
            Appointment.payment_status,
        )
        .having((Service.price - paid_total) > 0)
        .order_by(Appointment.date, Appointment.id)
        .all()
    )


def payment_export_rows(db, start_date, end_date, barber_id=None):
    query = (
        db.query(Payment, Appointment, Client, User, Service)
        .join(Appointment, Payment.appointment_id == Appointment.id)
        .join(Client, Payment.client_id == Client.id)
        .join(User, Appointment.user_id == User.id)
        .join(Service, Appointment.service_id == Service.id)
        .filter(
            or_(
                (
                    Payment.status.in_(PAID_PAYMENT_STATUSES)
                    & Payment.paid_at.isnot(None)
                    & func.date(Payment.paid_at).between(start_date, end_date)
                ),
                (
                    (Payment.status == "refunded")
                    & Payment.refunded_at.isnot(None)
                    & func.date(Payment.refunded_at).between(start_date, end_date)
                ),
            )
        )
    )

    if barber_id is not None:
        query = query.filter(Appointment.user_id == barber_id)

    return query.order_by(Payment.created_at, Payment.id).all()


def frequent_clients(db, start_date, end_date):
    return (
        db.query(
            Client.id.label("client_id"),
            Client.name.label("client"),
            func.count(Appointment.id).label("visitas"),
        )
        .join(Appointment, Appointment.client_id == Client.id)
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date),
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
            func.count(Appointment.id).label("no_show"),
        )
        .join(Appointment, Appointment.client_id == Client.id)
        .filter(
            Appointment.status == "no_show",
            Appointment.date.between(start_date, end_date),
        )
        .group_by(Client.id, Client.name)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )


def demand_by_hour(db, start_date, end_date):
    hour_bucket = hour_bucket_expression(db_dialect_name(db))
    return (
        db.query(
            hour_bucket,
            func.count(Appointment.id).label("total"),
        )
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date),
        )
        .group_by(hour_bucket)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )


def demand_by_weekday(db, start_date, end_date):
    weekday_bucket = weekday_bucket_expression(db_dialect_name(db))
    return (
        db.query(
            weekday_bucket,
            func.count(Appointment.id).label("total"),
        )
        .filter(
            Appointment.status == "completada",
            Appointment.date.between(start_date, end_date),
        )
        .group_by(weekday_bucket)
        .order_by(func.count(Appointment.id).desc())
        .all()
    )
