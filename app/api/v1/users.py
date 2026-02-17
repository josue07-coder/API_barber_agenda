from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schema.user import UserUpdate, UserResponse
from app.services.user_service import *
from app.core.dependecies import require_role, get_current_user

router = APIRouter()

@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db),
     _=Depends(require_role("admin"))):
    return get_all_users(db)

@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db),
     _=Depends(require_role("admin"))):
    return get_user_by_id_or_404(db, user_id)

@router.get("/email/{email}", response_model=UserResponse)
def get_user_email(email: str, db: Session = Depends(get_db),
    _=Depends(require_role("admin"))):
    return get_user_by_email_or_404(db, email)

@router.put("/{user_id}", response_model=UserResponse)
def update_user_api(user_id: int, data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):
    return update_user(db, user_id, data, current_user)

@router.delete("/{user_id}/deactivate")
def deactivate_user_api(
    user_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))):
    deactivate_user(db, user_id)
    return {"message": "Usuario desactivado"}
