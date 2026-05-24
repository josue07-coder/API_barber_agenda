from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class BranchSettings(Base):
    __tablename__ = "branch_settings"

    branch_id = Column(Integer, ForeignKey("branches.id"), primary_key=True)
    timezone = Column(String(64), default="America/Santo_Domingo", nullable=False)
    currency = Column(String(3), default="DOP", nullable=False)
    default_cancel_cutoff_hours = Column(Integer, default=24, nullable=False)
    default_reschedule_cutoff_hours = Column(Integer, default=24, nullable=False)
    deposit_required = Column(Boolean, default=False, nullable=False)
    default_deposit_amount = Column(Numeric(10, 2), nullable=True)
    default_deposit_percentage = Column(Numeric(5, 2), nullable=True)
    reminder_24h_enabled = Column(Boolean, default=True, nullable=False)
    reminder_2h_enabled = Column(Boolean, default=True, nullable=False)
    no_show_penalty_points = Column(Integer, default=3, nullable=False)
    no_show_penalty_amount = Column(Numeric(10, 2), nullable=True)
    late_cancel_penalty_points = Column(Integer, default=1, nullable=False)
    late_cancel_penalty_amount = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    branch = relationship("Branch")
