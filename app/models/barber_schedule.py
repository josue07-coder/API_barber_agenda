from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Time
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class BarberSchedule(Base):
    __tablename__ = "barber_schedules"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_barber_schedules_weekday"),
        CheckConstraint("start_time < end_time", name="ck_barber_schedules_time_range"),
        CheckConstraint(
            "(break_start_time IS NULL AND break_end_time IS NULL) OR "
            "(break_start_time IS NOT NULL AND break_end_time IS NOT NULL AND "
            "break_start_time < break_end_time AND "
            "break_start_time >= start_time AND break_end_time <= end_time)",
            name="ck_barber_schedules_break_range",
        ),
        Index("ix_barber_schedules_barber_weekday", "barber_id", "weekday"),
    )

    id = Column(Integer, primary_key=True, index=True)
    barber_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weekday = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_start_time = Column(Time, nullable=True)
    break_end_time = Column(Time, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    barber = relationship("User")
