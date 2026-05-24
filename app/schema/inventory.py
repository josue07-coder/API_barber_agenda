from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.payment_method import PaymentMethod


class ProductCreate(BaseModel):
    branch_id: Optional[int] = None
    name: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    sku: str = Field(min_length=2, max_length=80)
    barcode: Optional[str] = Field(default=None, max_length=80)
    category: Optional[str] = Field(default=None, max_length=80)
    brand: Optional[str] = Field(default=None, max_length=80)
    cost_price: Decimal = Field(ge=0)
    sale_price: Decimal = Field(ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    min_stock_alert: int = Field(default=0, ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "branch_id": 1,
                "name": "Pomada mate",
                "sku": "POM-MATE-001",
                "cost_price": "200.00",
                "sale_price": "450.00",
                "stock_quantity": 10,
                "min_stock_alert": 3,
            }
        }
    )


class ProductUpdate(BaseModel):
    branch_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)
    barcode: Optional[str] = Field(default=None, max_length=80)
    category: Optional[str] = Field(default=None, max_length=80)
    brand: Optional[str] = Field(default=None, max_length=80)
    cost_price: Optional[Decimal] = Field(default=None, ge=0)
    sale_price: Optional[Decimal] = Field(default=None, ge=0)
    min_stock_alert: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    branch_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    cost_price: Decimal
    sale_price: Decimal
    stock_quantity: int
    min_stock_alert: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})


class InventoryMovementCreate(BaseModel):
    product_id: int
    movement_type: str = Field(pattern="^(purchase|adjustment|loss|refund)$")
    quantity: int = Field(gt=0)
    unit_cost: Optional[Decimal] = Field(default=None, ge=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    reference_type: Optional[str] = Field(default=None, max_length=50)
    reference_id: Optional[int] = None


class InventoryMovementResponse(BaseModel):
    id: int
    product_id: int
    branch_id: Optional[int] = None
    movement_type: str
    quantity: int
    previous_stock: int
    new_stock: int
    unit_cost: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    created_by_user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})


class ProductSaleCreate(BaseModel):
    product_id: int
    branch_id: Optional[int] = None
    client_id: Optional[int] = None
    payment_id: Optional[int] = None
    quantity: int = Field(gt=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)
    payment_method: PaymentMethod = PaymentMethod.cash


class ProductSaleResponse(BaseModel):
    id: int
    branch_id: Optional[int] = None
    product_id: int
    client_id: Optional[int] = None
    payment_id: Optional[int] = None
    cash_session_id: Optional[int] = None
    quantity: int
    unit_price: Decimal
    total_amount: Decimal
    sold_by_user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, json_encoders={Decimal: float})
