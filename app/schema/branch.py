from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BranchBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)


class BranchCreate(BranchBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Sucursal Centro",
                "address": "Av. Principal #10",
                "phone": "8095550000"
            }
        }
    )


class BranchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    address: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    is_active: Optional[bool] = None


class BranchResponse(BranchBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
