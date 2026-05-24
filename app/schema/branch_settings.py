from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BranchSettingsBase(BaseModel):
    timezone: str = Field(default="America/Santo_Domingo", min_length=2, max_length=64)
    currency: str = Field(default="DOP", min_length=3, max_length=3)
    default_cancel_cutoff_hours: int = Field(default=24, ge=0)
    default_reschedule_cutoff_hours: int = Field(default=24, ge=0)
    deposit_required: bool = False
    default_deposit_amount: Optional[Decimal] = Field(default=None, ge=0)
    default_deposit_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100)
    reminder_24h_enabled: bool = True
    reminder_2h_enabled: bool = True
    no_show_penalty_points: int = Field(default=3, ge=0)
    no_show_penalty_amount: Optional[Decimal] = Field(default=None, ge=0)
    late_cancel_penalty_points: int = Field(default=1, ge=0)
    late_cancel_penalty_amount: Optional[Decimal] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_deposit_defaults(self):
        if self.default_deposit_amount is not None and self.default_deposit_percentage is not None:
            raise ValueError("Usa monto o porcentaje de deposito, no ambos")
        return self


class BranchSettingsUpdate(BranchSettingsBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timezone": "America/Santo_Domingo",
                "currency": "DOP",
                "default_cancel_cutoff_hours": 12,
                "default_reschedule_cutoff_hours": 12,
                "deposit_required": True,
                "default_deposit_amount": "250.00",
                "default_deposit_percentage": None,
                "reminder_24h_enabled": True,
                "reminder_2h_enabled": False,
                "no_show_penalty_points": 3,
                "no_show_penalty_amount": "250.00",
                "late_cancel_penalty_points": 1,
                "late_cancel_penalty_amount": "100.00"
            }
        }
    )


class BranchSettingsResponse(BranchSettingsBase):
    branch_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},
    )
