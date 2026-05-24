from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.session import get_db
from app.schema.client import (
    ClientCreate,
    ClientUpdate, 
    ClientResponse
)
from app.schema.client_penalty import ClientPenaltyCreate, ClientPenaltyResponse
from app.services.client_service import (
    update_existing_client,
    create_client,
    list_clients,
    get_client_by_id,
    deactivate_client
)
from app.api.deps import get_current_user, require_role
from app.services.client_penalty_service import create_manual_penalty, list_client_penalties

router = APIRouter()

@router.post("/", response_model=ClientResponse)
def create_client_api(data: ClientCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)):

    return create_client(db, data)

@router.get("/", response_model=List[ClientResponse])
def get_clients_api(
    search: Optional[str] = Query(
        None,
        description="Buscar cliente por nombre"
    ),
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))
):
    return list_clients(db, search)

@router.get("/{client_id}", response_model=ClientResponse)
def get_client_api(client_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))):
    return get_client_by_id(db, client_id)


@router.get(
    "/{client_id}/penalties",
    response_model=List[ClientPenaltyResponse],
    summary="Listar penalizaciones de cliente",
    description="Admin ve todas; barber ve penalizaciones relacionadas con sus citas; client solo las propias.",
)
def get_client_penalties_api(
    client_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return list_client_penalties(db, client_id, current_user)


@router.post(
    "/{client_id}/penalties",
    response_model=ClientPenaltyResponse,
    summary="Crear penalizacion manual",
    description="Crea una penalizacion manual para un cliente. Requiere admin.",
)
def create_client_penalty_api(
    client_id: int,
    data: ClientPenaltyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return create_manual_penalty(db, client_id, data, current_user)

@router.put("/{client_id}", response_model=ClientResponse)
def update_client_api(client_id: int, 
    data: ClientUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))):

    return update_existing_client(db, client_id, data)

@router.put("/delete/{client_id}")
def deactivate_client_api(client_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_role("admin"))):
    deactivate_client(db, client_id)
    return {"message": "Cliente eliminado"}
