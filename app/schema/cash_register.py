from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment_method import PaymentMethod


class CashSessionOpen(BaseModel):
    branch_id: int
    opening_amount: Decimal = Field(ge=0)
    notes: Optional[str] = Field(default=None, max_length=255)


class CashSessionClose(BaseModel):
    closing_amount: Decimal = Field(ge=0)
    notes: Optional[str] = Field(default=None, max_length=255)


class CashSessionResponse(BaseModel):
    id: int
    branch_id: int
    opened_by_user_id: int
    closed_by_user_id: Optional[int] = None
    opening_amount: Decimal
    closing_amount: Optional[Decimal] = None
    expected_amount: Optional[Decimal] = None
    difference_amount: Optional[Decimal] = None
    status: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})


class CashMovementCreate(BaseModel):
    cash_session_id: int
    movement_type: str = Field(pattern="^(income|expense|adjustment|refund)$")
    amount: Decimal = Field(gt=0)
    method: PaymentMethod = PaymentMethod.cash
    description: Optional[str] = Field(default=None, max_length=255)


class CashMovementResponse(BaseModel):
    id: int
    cash_session_id: int
    payment_id: Optional[int] = None
    movement_type: str
    amount: Decimal
    method: PaymentMethod
    description: Optional[str] = None
    created_by_user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})
