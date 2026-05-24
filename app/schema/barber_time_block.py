from datetime import date, time
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BarberTimeBlockBase(BaseModel):
    barber_id: int
    date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = Field(default=None, max_length=255)
    is_full_day: bool = False
    is_active: bool = True

    @model_validator(mode="after")
    def validate_block(self):
        if self.is_full_day:
            if self.start_time is not None or self.end_time is not None:
                raise ValueError("Un bloqueo de dia completo no debe incluir horas")
            return self

        if self.start_time is None or self.end_time is None:
            raise ValueError("Un bloqueo parcial requiere start_time y end_time")

        if self.start_time >= self.end_time:
            raise ValueError("start_time debe ser menor que end_time")

        return self


class BarberTimeBlockCreate(BarberTimeBlockBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "barber_id": 2,
                "date": "2026-06-03",
                "start_time": "15:00:00",
                "end_time": "16:00:00",
                "reason": "Cita personal",
                "is_full_day": False,
                "is_active": True
            }
        }
    )


class BarberTimeBlockUpdate(BaseModel):
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = Field(default=None, max_length=255)
    is_full_day: Optional[bool] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reason": "Bloqueo actualizado",
                "is_active": True
            }
        }
    )


class BarberTimeBlockResponse(BarberTimeBlockBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
