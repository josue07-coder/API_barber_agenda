from sqlalchemy import CheckConstraint, Column, DateTime, Index, Integer, String
from sqlalchemy import func

from app.database.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('email', 'sms', 'whatsapp', 'in_app')",
            name="ck_notifications_channel_allowed",
        ),
        CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'cancelled')",
            name="ck_notifications_status_allowed",
        ),
        Index("ix_notifications_recipient", "recipient_type", "recipient_id"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_channel", "channel"),
        Index("ix_notifications_scheduled_for", "scheduled_for"),
        Index("ix_notifications_related", "related_type", "related_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    recipient_type = Column(String(30), nullable=False)
    recipient_id = Column(Integer, nullable=False)
    channel = Column(String(20), nullable=False)
    subject = Column(String(160), nullable=False)
    message = Column(String(1000), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    related_type = Column(String(50), nullable=True)
    related_id = Column(Integer, nullable=True)
    scheduled_for = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
