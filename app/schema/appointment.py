from pydantic import BaseModel, Field
from datetime import datetime, date as dat, time
from typing import Any, Optional, List
from pydantic import ConfigDict

from app.models.appointment_status import AppointmentStatus


class AppointmentCreate(BaseModel):
    barber_id: int
    client_id: int
    service_id: int
    date: dat
    start_time: time
    branch_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "barber_id": 2,
                "client_id": 1,
                "service_id": 1,
                "date": "2026-06-01",
                "start_time": "10:00:00"
            }
        }
    )

class AppointmentUpdate(BaseModel):
     date: Optional[dat] = None
     start_time: Optional[time] = None


class AppointmentCancel(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reason": "Cliente solicito cancelar"
            }
        }
    )


class AppointmentReschedule(BaseModel):
    date: dat
    start_time: time

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2026-06-02",
                "start_time": "14:00:00"
            }
        }
    )
       

class AppointmentResponse(BaseModel):
    id: int
    date: dat
    start_time: time
    end_time: time
    status: str
    payment_status: str

    user_id: int
    client_id: int
    service_id: int
    branch_id: Optional[int] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by_user_id: Optional[int] = None
    cancellation_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AvailableSlotsResponse(BaseModel):
     slots: List[time]

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentHistoryResponse(BaseModel):
    id: int
    appointment_id: int
    action: str
    old_values: Optional[dict[str, Any]] = None
    new_values: Optional[dict[str, Any]] = None
    changed_by_user_id: int
    reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
