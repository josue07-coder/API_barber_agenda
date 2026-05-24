from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class CashMovement(Base):
    __tablename__ = "cash_movements"
    __table_args__ = (
        CheckConstraint(
            "movement_type IN ('income', 'expense', 'adjustment', 'refund')",
            name="ck_cash_movements_type_allowed",
        ),
        CheckConstraint(
            "method IN ('cash', 'card', 'transfer', 'online', 'other')",
            name="ck_cash_movements_method_allowed",
        ),
        CheckConstraint("amount > 0", name="ck_cash_movements_amount_positive"),
        Index("ix_cash_movements_session", "cash_session_id"),
        Index("ix_cash_movements_payment", "payment_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    movement_type = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(String(20), nullable=False)
    description = Column(String(255), nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cash_session = relationship("CashSession")
    payment = relationship("Payment")
    created_by = relationship("User")
