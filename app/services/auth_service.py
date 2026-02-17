from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repo import (
    get_user_by_email,
    create_user
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)


def register_admin(
    db: Session,
    *,
    name: str,
    email: str,
    password: str
) -> dict:
    if get_user_by_email(db, email):
        raise ValueError("Email ya registrado")

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="admin",
        is_active=True,
    )

    user = create_user(db, user)

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }


def register_barber(
    db: Session,
    *,
    name: str,
    email: str,
    password: str
) -> User:
    if get_user_by_email(db, email):
        raise ValueError("Email ya registrado")

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="barber",
        is_active=True,
    )

    user = create_user(db, user)

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }


def login_user(
    db: Session,
    *,
    email: str,
    password: str
) -> dict:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.password):
        raise ValueError("Credenciales inválidas")

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }
