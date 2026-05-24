from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from pydantic import ConfigDict
from app.models.user_role import UserRole


class UserBase(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Admin Principal",
                "email": "admin@barber.local",
                "password": "Admin12345"
            }
        }
    )


class ClientRegister(UserCreate):
    phone: str = Field(min_length=7, max_length=15)
    notes: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Juan Perez",
                "email": "juan@barber.local",
                "password": "Client12345",
                "phone": "8095551234",
                "notes": "Prefiere corte bajo"
            }
        }
    )
   
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Carlos Barber",
                "role": "barber",
                "is_active": True
            }
        }
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserResponse(UserBase):
    id: int
    role: UserRole
    client_id: Optional[int] = None
    branch_id: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
