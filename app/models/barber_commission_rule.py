from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class BarberCommissionRule(Base):
    __tablename__ = "barber_commission_rules"
    __table_args__ = (
        CheckConstraint("commission_type IN ('percentage', 'fixed')", name="ck_commission_rules_type_allowed"),
        CheckConstraint("commission_value >= 0", name="ck_commission_rules_value_nonnegative"),
        Index("ix_commission_rules_barber", "barber_id"),
        Index("ix_commission_rules_branch", "branch_id"),
        Index("ix_commission_rules_service", "service_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    commission_type = Column(String(20), nullable=False)
    commission_value = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    barber = relationship("User", foreign_keys=[barber_id])
    branch = relationship("Branch")
    service = relationship("Service")
