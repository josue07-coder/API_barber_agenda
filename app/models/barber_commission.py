from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class BarberCommission(Base):
    __tablename__ = "barber_commissions"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'paid', 'cancelled')", name="ck_barber_commissions_status_allowed"),
        CheckConstraint("base_amount >= 0", name="ck_barber_commissions_base_nonnegative"),
        CheckConstraint("commission_amount >= 0", name="ck_barber_commissions_amount_nonnegative"),
        Index("ix_barber_commissions_barber", "barber_id"),
        Index("ix_barber_commissions_branch", "branch_id"),
        Index("ix_barber_commissions_status", "status"),
        Index("ix_barber_commissions_payment", "payment_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), unique=True, nullable=False)
    barber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    base_amount = Column(Numeric(10, 2), nullable=False)
    commission_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(255), nullable=True)

    appointment = relationship("Appointment")
    payment = relationship("Payment")
    barber = relationship("User", foreign_keys=[barber_id])
    approved_by = relationship("User", foreign_keys=[approved_by_user_id])
    branch = relationship("Branch")
    service = relationship("Service")
