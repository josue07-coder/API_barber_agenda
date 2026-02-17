from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schema.client import ClientCreate, ClientUpdate
from app.models.client import Client
from app.repositories.client_repo import (
    get_clients,
    get_client_by_id,
    create_client,
    update_client,
    deactivate_client as deactivate_client_repo
)

def create_new_client(db: Session, data: ClientCreate):
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
