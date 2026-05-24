from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Time
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class BarberTimeBlock(Base):
    __tablename__ = "barber_time_blocks"
    __table_args__ = (
        CheckConstraint(
            "(is_full_day = true AND start_time IS NULL AND end_time IS NULL) OR "
            "(is_full_day = false AND start_time IS NOT NULL AND end_time IS NOT NULL AND start_time < end_time)",
            name="ck_barber_time_blocks_range",
        ),
        Index("ix_barber_time_blocks_barber_date", "barber_id", "date"),
        Index("ix_barber_time_blocks_date", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    reason = Column(String(255), nullable=True)
    is_full_day = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    barber = relationship("User")
