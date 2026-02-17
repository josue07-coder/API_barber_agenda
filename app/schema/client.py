from pydantic import BaseModel, Field
from typing import Optional
from pydantic import ConfigDict

class ClientBase(BaseModel):
    name: str = Field(min_length=2)
    phone: str = Field(min_length=7, max_length=15)
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[str] = None

class ClientResponse(ClientBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
