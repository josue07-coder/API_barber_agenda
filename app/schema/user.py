from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from pydantic import ConfigDict


class UserBase(BaseModel):
    name: str = Field(min_length=2)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6)
   
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
