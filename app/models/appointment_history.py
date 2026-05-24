from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class AppointmentHistory(Base):
    __tablename__ = "appointment_history"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False, index=True)
    action = Column(String(30), nullable=False)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointment = relationship("Appointment", back_populates="history")
    changed_by = relationship("User")
