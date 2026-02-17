from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from pydantic import ConfigDict

class ServiceBase(BaseModel):
    name: str = Field(min_length=2)
    duration_minutes: int = Field(gt=0)
    price: Decimal = Field(gt=0)

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2)
    duration_minutes: Optional[int] = Field(default=None, gt=0)
    price: Optional[Decimal] = Field(default=None, gt=0)
    is_active: Optional[bool] = None


class ServiceResponse(ServiceBase):
    id: int
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={Decimal: float}
    )
