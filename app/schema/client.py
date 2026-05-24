from pydantic import BaseModel, Field
from typing import Optional
from pydantic import ConfigDict

class ClientBase(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7, max_length=15)
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Juan Perez",
                "phone": "8095551234",
                "notes": "Prefiere corte bajo"
            }
        }
    )

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "8095559876",
                "notes": "Cliente frecuente"
            }
        }
    )

class ClientResponse(ClientBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ClientProfileUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2)
    phone: Optional[str] = Field(default=None, min_length=7, max_length=15)
    notes: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "name": "Juan Perez",
                "phone": "8095559876",
                "notes": "Prefiere la tarde"
            }
        }
    )
