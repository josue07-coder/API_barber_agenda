from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        CheckConstraint(
            "status IN ('pending', 'paid', 'partially_paid', 'refunded', 'failed', 'cancelled')",
            name="ck_payments_status_allowed",
        ),
        CheckConstraint(
            "payment_method IN ('cash', 'card', 'transfer', 'online', 'other')",
            name="ck_payments_method_allowed",
        ),
        Index("ix_payments_appointment_id", "appointment_id"),
        Index("ix_payments_client_id", "client_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_paid_at", "paid_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="DOP", nullable=False)
    payment_method = Column(String(20), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    transaction_reference = Column(String(120), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    appointment = relationship("Appointment", back_populates="payments")
    client = relationship("Client")
