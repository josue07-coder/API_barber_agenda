from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.inventory import InventoryMovementCreate, InventoryMovementResponse
from app.services.inventory_service import create_manual_movement, get_movements


router = APIRouter()


@router.post("/movements", response_model=InventoryMovementResponse)
def create_movement_api(
    data: InventoryMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_manual_movement(db, data, current_user)


@router.get("/movements", response_model=list[InventoryMovementResponse])
def list_movements_api(
    product_id: int | None = Query(default=None),
    branch_id: int | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_movements(db, current_user, product_id, branch_id, start_date, end_date)
