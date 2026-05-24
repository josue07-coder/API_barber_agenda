from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment_method import PaymentMethod
from app.models.payment_status import PaymentStatus


class PaymentCreate(BaseModel):
    appointment_id: int
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="DOP", min_length=3, max_length=3)
    payment_method: PaymentMethod
    status: PaymentStatus = PaymentStatus.paid
    transaction_reference: Optional[str] = Field(default=None, max_length=120)
    notes: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "appointment_id": 1,
                "amount": "250.00",
                "currency": "DOP",
                "payment_method": "cash",
                "status": "paid",
                "transaction_reference": "RCPT-0001",
                "notes": "Deposito inicial"
            }
        }
    )


class PaymentResponse(BaseModel):
    id: int
    appointment_id: int
    client_id: int
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_reference: Optional[str] = None
    paid_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float},
    )


class PaymentMarkPaid(BaseModel):
    transaction_reference: Optional[str] = Field(default=None, max_length=120)
    notes: Optional[str] = Field(default=None, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "transaction_reference": "AUTH-12345",
                "notes": "Pago confirmado"
            }
        }
    )


class PaymentRefund(BaseModel):
    reason: str = Field(min_length=2, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reason": "Cliente solicito reembolso"
            }
        }
    )


class PaymentSummaryResponse(BaseModel):
    total_payments: int
    total_paid: float
    total_refunded: float
    currency: str
