from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schema.user import UserCreate, TokenResponse, UserResponse
from app.services.auth_service import (
    register_admin,
    register_barber,
    login_user,
)
from app.core.dependecies import require_role

router = APIRouter()

#  Registrar ADMIN
@router.post("/register", response_model=TokenResponse)
def register_admin_api(
    data: UserCreate,
    db: Session = Depends(get_db),
    _= Depends(require_role("admin"))
):
    try:
        return register_admin(
            db,
            name=data.name,
            email=data.email,
            password=data.password
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


#  Registrar BARBERO (solo admin)
@router.post("/barbers", response_model=UserResponse)
def create_barber_api(
    data: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin")),
):
    try:
        return register_barber(
            db,
            name=data.name,
            email=data.email,
            password=data.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


#  Login
@router.post("/login", response_model=TokenResponse)
def login_api(
    data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    try:
        return login_user(
            db, 
            email=data.username,
            password=data.password
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Credenciales inválidas")
