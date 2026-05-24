from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.inventory import ProductCreate, ProductResponse, ProductUpdate
from app.services.inventory_service import (
    create_new_product,
    deactivate_product,
    get_low_stock,
    get_product,
    get_products,
    update_existing_product,
)


router = APIRouter()


@router.post("/", response_model=ProductResponse)
def create_product_api(data: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_new_product(db, data, current_user)


@router.get("/", response_model=list[ProductResponse])
def list_products_api(
    branch_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_products(db, current_user, branch_id)


@router.get("/low-stock", response_model=list[ProductResponse])
def low_stock_api(
    branch_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_low_stock(db, current_user, branch_id)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product_api(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_product(db, product_id, current_user)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product_api(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_existing_product(db, product_id, data, current_user)


@router.patch("/{product_id}/deactivate", response_model=ProductResponse)
def deactivate_product_api(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return deactivate_product(db, product_id, current_user)
