from pydantic import BaseModel
from datetime import date as dat, time
from typing import Optional, List
from pydantic import ConfigDict

from app.models.appointment_status import AppointmentStatus


class AppointmentCreate(BaseModel):
    barber_id: int
    client_id: int
    service_id: int
    date: dat
    start_time: time

class AppointmentUpdate(BaseModel):
     date: Optional[dat] = None
     start_time: Optional[time] = None
       

class AppointmentResponse(BaseModel):
    id: int
    date: dat
    start_time: time
    end_time: time
    status: str

    user_id: int
    client_id: int
    service_id: int

    model_config = ConfigDict(from_attributes=True)

class AvailableSlotsResponse(BaseModel):
     slots: List[time]

class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus