from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.schema.service import ServiceCreate, ServiceUpdate
from app.models.service import Service
from app.repositories.service_repo import (
    get_services,
    get_service_by_id,
    create_service,
    update_service,
    deactivate_service as deactivate_service_repo
)

def create_new_service(db: Session, data: ServiceCreate):
    service = Service(
        name=data.name,
        duration_minutes=data.duration_minutes,
        price=data.price,
        is_active=True
    )
    return create_service(db, service)

def get_service_id(db: Session, service_id: int):
    service = get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(404, "Servicio no encontrado")
    return service

def list_service(db: Session, search: str | None = None):
    return get_services(db, search)

def update_existing_service(
    db: Session,
    service_id: int,
    data: ServiceUpdate
):
    service = get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(404, "Servicio no encontrado")

    if data.name is not None:
        service.name = data.name

    if data.duration_minutes is not None:
        service.duration_minutes = data.duration_minutes

    if data.price is not None:
        service.price = data.price

    if data.is_active is not None:
        service.is_active = data.is_active

    return update_service(db, service)

def deactivate_service(db: Session, service_id: int):
    service = get_service_by_id(db, service_id)
    if not service:
        raise HTTPException(404, "Servicio no encontrado")

    return deactivate_service_repo(db, service)
