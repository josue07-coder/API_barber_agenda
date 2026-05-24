from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class CashSession(Base):
    __tablename__ = "cash_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('open', 'closed')", name="ck_cash_sessions_status_allowed"),
        CheckConstraint("opening_amount >= 0", name="ck_cash_sessions_opening_amount_nonnegative"),
        CheckConstraint("closing_amount IS NULL OR closing_amount >= 0", name="ck_cash_sessions_closing_amount_nonnegative"),
        Index("ix_cash_sessions_branch_status", "branch_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    opened_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    closed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    opening_amount = Column(Numeric(10, 2), nullable=False)
    closing_amount = Column(Numeric(10, 2), nullable=True)
    expected_amount = Column(Numeric(10, 2), nullable=True)
    difference_amount = Column(Numeric(10, 2), nullable=True)
    status = Column(String(20), default="open", nullable=False)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String(255), nullable=True)

    branch = relationship("Branch")
    opened_by = relationship("User", foreign_keys=[opened_by_user_id])
    closed_by = relationship("User", foreign_keys=[closed_by_user_id])
