from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CommissionRuleCreate(BaseModel):
    barber_id: int
    branch_id: Optional[int] = None
    service_id: Optional[int] = None
    commission_type: str = Field(pattern="^(percentage|fixed)$")
    commission_value: Decimal = Field(ge=0)
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValueError("starts_at debe ser menor que ends_at")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "barber_id": 2,
                "branch_id": 1,
                "service_id": None,
                "commission_type": "percentage",
                "commission_value": "10.00",
            }
        }
    )


class CommissionRuleUpdate(BaseModel):
    branch_id: Optional[int] = None
    service_id: Optional[int] = None
    commission_type: Optional[str] = Field(default=None, pattern="^(percentage|fixed)$")
    commission_value: Optional[Decimal] = Field(default=None, ge=0)
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "commission_type": "fixed",
                "commission_value": "150.00",
                "is_active": True,
            }
        }
    )


class CommissionRuleResponse(BaseModel):
    id: int
    barber_id: int
    branch_id: Optional[int] = None
    service_id: Optional[int] = None
    commission_type: str
    commission_value: Decimal
    is_active: bool
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})


class CommissionResponse(BaseModel):
    id: int
    appointment_id: int
    payment_id: int
    barber_id: int
    branch_id: Optional[int] = None
    service_id: int
    base_amount: Decimal
    commission_amount: Decimal
    status: str
    calculated_at: datetime
    approved_by_user_id: Optional[int] = None
    paid_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})
