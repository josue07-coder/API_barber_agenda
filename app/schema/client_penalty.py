from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClientPenaltyCreate(BaseModel):
    appointment_id: Optional[int] = None
    penalty_type: str = Field(default="manual", pattern="^(no_show|late_cancel|manual)$")
    reason: str = Field(min_length=2, max_length=255)
    amount: Optional[Decimal] = Field(default=None, ge=0)
    points: int = Field(default=1, ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "appointment_id": 10,
                "penalty_type": "manual",
                "reason": "Incumplimiento recurrente",
                "amount": "100.00",
                "points": 1,
            }
        }
    )


class PenaltyResolution(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={"example": {"reason": "Resuelto por administracion"}}
    )


class ClientPenaltyResponse(BaseModel):
    id: int
    client_id: int
    appointment_id: Optional[int] = None
    penalty_type: str
    reason: str
    amount: Optional[Decimal] = None
    points: int
    status: str
    created_by_user_id: int
    forgiven_by_user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},
    )
