from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repositories.user_repo import (
    get_all_users as repo_get_all_users,
    get_user_by_id,
    get_user_by_email,
    deactivate_user as deactivate_user_repo,
    update_user as update_user_repo
)
from app.schema.user import UserUpdate
from app.models.user import User
from app.models.user_role import UserRole
from app.core.security import hash_password
from app.services.branch_service import get_active_branch_or_404


def get_all_users(db:Session):
        return repo_get_all_users(db)

def get_user_by_id_or_404(db: Session, user_id: int):
        user = get_user_by_id(db, user_id)
        if not user:
                raise HTTPException(404, "Usuario no encontrado")
        return user

def get_user_by_email_or_404(db: Session, email: str):
        user = get_user_by_email(db, email)
        if not user:
                raise HTTPException(404, "Usuario no encontrado")
        return user

def update_user(db: Session, user_id: int, data: UserUpdate, current_user: User):
        user = get_user_by_id(db, user_id)
        if not user:
                raise HTTPException(404, "Usuario no encontrado")
        
        if current_user.role != "admin" and current_user.id != user_id:
                raise HTTPException(403, "No tienes permiso para editar este usuario")

        if data.name is not None:
                user.name = data.name

        if data.email is not None:
                user.email = data.email

        if data.password is not None:
                user.password = hash_password(data.password)

        if current_user.role == "admin":
                if data.role is not None:
                        user.role = data.role.value

                if data.branch_id is not None:
                        get_active_branch_or_404(db, data.branch_id)
                        user.branch_id = data.branch_id

                if data.is_active is not None:
                        user.is_active = data.is_active
        else:
                if data.role is not None or data.is_active is not None:
                        raise HTTPException(403, "No tienes permiso para modificar rol o estado")

        return update_user_repo(db, user)

def deactivate_user(db: Session, user_id: int):
        user = get_user_by_id(db, user_id)
        if not user:
                raise HTTPException(404, "Usuario no encontrado")

        deactivate_user_repo(db, user)

