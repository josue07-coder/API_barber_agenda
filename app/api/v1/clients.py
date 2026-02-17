from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database.session import get_db
from app.schema.client import (
    ClientCreate,
    ClientUpdate, 
    ClientResponse
)
from app.services.client_service import (
    update_existing_client,
    create_client,
    list_clients,
    get_client_by_id,
    deactivate_client
)
from app.core.dependecies import get_current_user, require_role

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
