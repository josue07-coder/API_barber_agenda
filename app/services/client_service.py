from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schema.client import ClientCreate, ClientUpdate
from app.models.client import Client
from app.repositories.client_repo import (
    get_clients,
    get_client_by_id,
    get_client_by_phone,
    phone_exists_for_other_client,
    create_client,
    update_client,
    deactivate_client as deactivate_client_repo
)

def create_new_client(db: Session, data: ClientCreate):
    if get_client_by_phone(db, data.phone):
        raise HTTPException(409, "Telefono ya registrado")

    client = Client(
        name=data.name,
        phone=data.phone,
        notes=data.notes,
        is_active=True
    )
    return create_client(db, client)

def get_client_id(db: Session, client_id: int):
    client = get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")
    return client

def list_clients(db: Session, search: str | None = None):
    return get_clients(db, search)

def update_existing_client(
    db: Session,
    client_id: int,
    data: ClientUpdate
):
    client = get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    if data.name is not None:
        client.name = data.name

    if data.phone is not None:
        if data.phone != client.phone and phone_exists_for_other_client(db, data.phone, client.id):
            raise HTTPException(409, "Telefono ya registrado")
        client.phone = data.phone

    if data.notes is not None:
        client.notes = data.notes

    if data.is_active is not None:
        client.is_active = data.is_active

    return update_client(db, client)

def deactivate_client(db: Session, client_id: int):
    client = get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    return deactivate_client_repo(db, client)


def update_my_client_profile(db: Session, current_user, data):
    if current_user.role != "client" or current_user.client_id is None:
        raise HTTPException(403, "Usuario cliente requerido")

    client = get_client_by_id(db, current_user.client_id)
    if not client:
        raise HTTPException(404, "Cliente no encontrado")

    if data.phone is not None and data.phone != client.phone:
        if phone_exists_for_other_client(db, data.phone, client.id):
            raise HTTPException(409, "Telefono ya registrado")
        client.phone = data.phone

    if data.name is not None:
        client.name = data.name
        current_user.name = data.name

    if data.notes is not None:
        client.notes = data.notes

    db.add(current_user)
    return update_client(db, client)
