from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.notification_channel import NotificationChannel
from app.models.notification_status import NotificationStatus


class NotificationResponse(BaseModel):
    id: int
    recipient_type: str
    recipient_id: int
    channel: NotificationChannel
    subject: str
    message: str
    status: NotificationStatus
    related_type: Optional[str] = None
    related_id: Optional[int] = None
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class NotificationFailed(BaseModel):
    error_message: str = Field(min_length=2, max_length=500)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_message": "Proveedor externo no disponible"
            }
        }
    )


class GenerateRemindersResponse(BaseModel):
    created: int
