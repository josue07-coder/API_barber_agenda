from datetime import date

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.payment import Payment


PAID_STATUSES = ["paid", "partially_paid"]


def create_payment(db: Session, payment: Payment) -> Payment:
    try:
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment
    except IntegrityError:
        db.rollback()
        raise


def get_payment_by_id(db: Session, payment_id: int) -> Payment | None:
    return db.query(Payment).filter(Payment.id == payment_id).first()


def get_payments_by_appointment(db: Session, appointment_id: int) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.appointment_id == appointment_id)
        .order_by(Payment.created_at, Payment.id)
        .all()
    )


def get_payments_by_client(db: Session, client_id: int) -> list[Payment]:
    return (
        db.query(Payment)
        .filter(Payment.client_id == client_id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .all()
    )


def update_payment(db: Session, payment: Payment) -> Payment:
    try:
        db.commit()
        db.refresh(payment)
        return payment
    except IntegrityError:
        db.rollback()
        raise


def get_total_paid_for_appointment(db: Session, appointment_id: int):
    return (
        db.query(func.coalesce(func.sum(Payment.amount), 0))
        .filter(
            Payment.appointment_id == appointment_id,
            Payment.status.in_(PAID_STATUSES),
        )
        .scalar()
    )


def get_payment_summary(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str = "DOP",
):
    paid_query = db.query(Payment).filter(Payment.currency == currency)
    refunded_query = db.query(Payment).filter(Payment.currency == currency)

    if start_date is not None:
        paid_query = paid_query.filter(func.date(Payment.paid_at) >= start_date)
        refunded_query = refunded_query.filter(func.date(Payment.refunded_at) >= start_date)

    if end_date is not None:
        paid_query = paid_query.filter(func.date(Payment.paid_at) <= end_date)
        refunded_query = refunded_query.filter(func.date(Payment.refunded_at) <= end_date)

    total_paid = (
        paid_query
        .filter(Payment.status.in_(PAID_STATUSES), Payment.paid_at.isnot(None))
        .with_entities(func.coalesce(func.sum(Payment.amount), 0))
        .scalar()
    )
    total_refunded = (
        refunded_query
        .filter(Payment.status == "refunded", Payment.refunded_at.isnot(None))
        .with_entities(func.coalesce(func.sum(Payment.amount), 0))
        .scalar()
    )
    total_payments = paid_query.filter(Payment.status.in_(PAID_STATUSES)).count()

    return {
        "total_payments": total_payments,
        "total_paid": float(total_paid or 0),
        "total_refunded": float(total_refunded or 0),
        "currency": currency,
    }
