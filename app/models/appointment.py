from sqlalchemy import CheckConstraint, Column, DateTime, Integer, Date, Time, String, ForeignKey, Index
from sqlalchemy import func
from sqlalchemy.orm import relationship
from app.database.base import Base

class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_user_date_start_time", "user_id", "date", "start_time"),
        Index("ix_appointments_client_date", "client_id", "date"),
        Index("ix_appointments_status", "status"),
        Index("ix_appointments_date", "date"),
        CheckConstraint(
            "status IN ('agendada', 'confirmada', 'completada', 'cancelada', 'no_show')",
            name="ck_appointments_status_allowed",
        ),
        CheckConstraint(
            "payment_status IN ('pending', 'paid', 'partially_paid', 'refunded', 'failed', 'cancelled')",
            name="ck_appointments_payment_status_allowed",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), default="agendada", nullable=False)
    payment_status = Column(String(20), default="pending", nullable=False)
    # scheduled | cancelled | completed
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)

    client = relationship("Client")
    service = relationship("Service")
    branch = relationship("Branch")
    user = relationship("User", foreign_keys=[user_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_user_id])
    history = relationship("AppointmentHistory", back_populates="appointment")
    payments = relationship("Payment", back_populates="appointment")
