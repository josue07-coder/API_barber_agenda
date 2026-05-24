from sqlalchemy.orm import Session

from app.models.user import User
from app.models.client import Client
from app.models.user_role import UserRole
from app.repositories.user_repo import (
    get_user_by_email,
    get_user_by_client_id,
    create_user
)
from app.repositories.client_repo import get_client_by_phone
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
        role=UserRole.admin.value,
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
        role=UserRole.barber.value,
        branch_id=None,
        is_active=True,
    )

    user = create_user(db, user)
    return user


def register_client(
    db: Session,
    *,
    name: str,
    email: str,
    password: str,
    phone: str,
    notes: str | None = None,
) -> dict:
    if get_user_by_email(db, email):
        raise ValueError("Email ya registrado")

    client = get_client_by_phone(db, phone)
    if client and get_user_by_client_id(db, client.id):
        raise ValueError("Telefono ya asociado a un usuario cliente")

    if not client:
        client = Client(
            name=name,
            phone=phone,
            notes=notes,
            is_active=True,
        )
        db.add(client)
        db.commit()
        db.refresh(client)

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role=UserRole.client.value,
        client_id=client.id,
        is_active=True,
    )

    user = create_user(db, user)

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role,
        "client_id": user.client_id,
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
        "client_id": user.client_id,
    })

    return {
        "access_token": token,
        "token_type": "bearer",
    }
