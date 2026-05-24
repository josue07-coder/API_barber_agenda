from datetime import time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BarberScheduleBase(BaseModel):
    barber_id: int
    weekday: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    break_start_time: Optional[time] = None
    break_end_time: Optional[time] = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_times(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time debe ser menor que end_time")

        has_break_start = self.break_start_time is not None
        has_break_end = self.break_end_time is not None
        if has_break_start != has_break_end:
            raise ValueError("break_start_time y break_end_time deben enviarse juntos")

        if has_break_start and has_break_end:
            if self.break_start_time >= self.break_end_time:
                raise ValueError("break_start_time debe ser menor que break_end_time")
            if self.break_start_time < self.start_time or self.break_end_time > self.end_time:
                raise ValueError("El descanso debe estar dentro del horario")

        return self


class BarberScheduleCreate(BarberScheduleBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "barber_id": 2,
                "weekday": 0,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "break_start_time": "12:00:00",
                "break_end_time": "13:00:00",
                "is_active": True
            }
        }
    )


class BarberScheduleUpdate(BaseModel):
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_start_time: Optional[time] = None
    break_end_time: Optional[time] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_time": "10:00:00",
                "end_time": "19:00:00",
                "is_active": True
            }
        }
    )


class BarberScheduleResponse(BarberScheduleBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
