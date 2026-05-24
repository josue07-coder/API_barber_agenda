from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class ClientPenalty(Base):
    __tablename__ = "client_penalties"
    __table_args__ = (
        CheckConstraint(
            "penalty_type IN ('no_show', 'late_cancel', 'manual')",
            name="ck_client_penalties_type_allowed",
        ),
        CheckConstraint(
            "status IN ('active', 'forgiven', 'paid', 'cancelled')",
            name="ck_client_penalties_status_allowed",
        ),
        CheckConstraint("points >= 0", name="ck_client_penalties_points_nonnegative"),
        CheckConstraint("amount IS NULL OR amount >= 0", name="ck_client_penalties_amount_nonnegative"),
        Index("ix_client_penalties_client_status", "client_id", "status"),
        Index("ix_client_penalties_appointment", "appointment_id"),
        Index("ix_client_penalties_type", "penalty_type"),
        Index("ix_client_penalties_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    penalty_type = Column(String(20), nullable=False)
    reason = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=True)
    points = Column(Integer, nullable=False)
    status = Column(String(20), default="active", nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    forgiven_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    client = relationship("Client")
    appointment = relationship("Appointment")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    forgiven_by = relationship("User", foreign_keys=[forgiven_by_user_id])
