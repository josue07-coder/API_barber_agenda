from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.session import get_db
from app.schema.service import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse
)
from app.services.service_service import (
    create_new_service,
    get_service_id,
    list_service,
    update_existing_service,
    deactivate_service
)
from app.core.dependecies import require_role, get_current_user

router = APIRouter()


# 🔹 Listar servicios (todos autenticados)
@router.get("/", response_model=List[ServiceResponse])
def list_services_api(
    search: Optional[str] = Query(None, description="Buscar servicio por nombre"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    return list_service(db, search)


# 🔹 Obtener servicio por ID
@router.get("/{service_id}", response_model=ServiceResponse)
def get_service_api(
    service_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    return get_service_id(db, service_id)


# 🔹 Crear servicio (solo admin)
@router.post("/", response_model=ServiceResponse)
def create_service_api(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    return create_new_service(db, data)


# 🔹 Actualizar servicio (solo admin)
@router.put("/{service_id}", response_model=ServiceResponse)
def update_service_api(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    return update_existing_service(db, service_id, data)


# 🔹 Desactivar servicio (soft delete)
@router.delete("/{service_id}", status_code=204)
def deactivate_service_api(
    service_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    deactivate_service(db, service_id)
