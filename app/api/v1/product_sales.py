from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schema.inventory import ProductSaleCreate, ProductSaleResponse
from app.services.inventory_service import create_sale, get_sales


router = APIRouter()


@router.post("/", response_model=ProductSaleResponse)
def create_product_sale_api(
    data: ProductSaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_sale(db, data, current_user)


@router.get("/", response_model=list[ProductSaleResponse])
def list_product_sales_api(
    branch_id: int | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_sales(db, current_user, branch_id, start_date, end_date)
