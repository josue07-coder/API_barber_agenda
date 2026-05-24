from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.rate_limit import check_login_rate_limit
from app.database.session import get_db
from app.schema.user import ClientRegister, UserCreate, TokenResponse, UserResponse
from app.services.auth_service import (
    register_admin,
    register_barber,
    register_client,
    login_user,
)
from app.repositories.user_repo import admin_exists
from app.api.deps import require_role

router = APIRouter()

#  Registrar ADMIN
@router.post("/register", response_model=TokenResponse)
def register_admin_api(
    data: UserCreate,
    db: Session = Depends(get_db),
):
    if admin_exists(db):
        raise HTTPException(
            status_code=403,
            detail="Ya existe un administrador registrado"
        )

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


@router.post("/register-client", response_model=TokenResponse)
def register_client_api(
    data: ClientRegister,
    db: Session = Depends(get_db),
):
    try:
        return register_client(
            db,
            name=data.name,
            email=data.email,
            password=data.password,
            phone=data.phone,
            notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


#  Login
@router.post("/login", response_model=TokenResponse)
def login_api(
    _: None = Depends(check_login_rate_limit),
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
