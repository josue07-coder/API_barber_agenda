from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cash_movement import CashMovement
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_sale import ProductSale
from app.models.user import User
from app.repositories.cash_register_repo import create_cash_movement, get_open_cash_session_by_branch
from app.repositories.client_repo import get_client_by_id
from app.repositories.inventory_repo import (
    create_inventory_movement,
    create_product,
    create_product_sale,
    get_product_by_id,
    get_product_by_sku,
    list_inventory_movements,
    list_product_sales,
    list_products,
    low_stock_products,
    product_income_by_branch,
    top_sold_products,
    update_product,
)
from app.repositories.payment_repo import get_payment_by_id
from app.schema.inventory import InventoryMovementCreate, ProductCreate, ProductSaleCreate, ProductUpdate
from app.services.branch_service import get_active_branch_or_404


def ensure_admin(current_user: User) -> None:
    if current_user.role != "admin":
        raise HTTPException(403, "No tienes permiso")


def ensure_inventory_access(db: Session, current_user: User, branch_id: int | None) -> None:
    if branch_id is not None:
        get_active_branch_or_404(db, branch_id)
    if current_user.role == "admin":
        return
    if current_user.role == "barber" and (branch_id is None or current_user.branch_id == branch_id):
        return
    raise HTTPException(403, "No tienes permiso para inventario")


def get_product_or_404(db: Session, product_id: int) -> Product:
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(404, "Producto no encontrado")
    return product


def create_new_product(db: Session, data: ProductCreate, current_user: User) -> Product:
    ensure_admin(current_user)
    if data.branch_id is not None:
        get_active_branch_or_404(db, data.branch_id)
    if get_product_by_sku(db, data.sku):
        raise HTTPException(409, "SKU ya existe")
    try:
        return create_product(db, Product(**data.model_dump(), is_active=True))
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "SKU ya existe")


def get_product(db: Session, product_id: int, current_user: User) -> Product:
    product = get_product_or_404(db, product_id)
    ensure_inventory_access(db, current_user, product.branch_id)
    return product


def get_products(db: Session, current_user: User, branch_id: int | None = None) -> list[Product]:
    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso")
    if current_user.role == "barber":
        branch_id = current_user.branch_id
    ensure_inventory_access(db, current_user, branch_id)
    return list_products(db, branch_id=branch_id)


def update_existing_product(db: Session, product_id: int, data: ProductUpdate, current_user: User) -> Product:
    ensure_admin(current_user)
    product = get_product_or_404(db, product_id)
    payload = data.model_dump(exclude_unset=True)
    if "branch_id" in payload and payload["branch_id"] is not None:
        get_active_branch_or_404(db, payload["branch_id"])
    for key, value in payload.items():
        setattr(product, key, value)
    return update_product(db, product)


def deactivate_product(db: Session, product_id: int, current_user: User) -> Product:
    ensure_admin(current_user)
    product = get_product_or_404(db, product_id)
    product.is_active = False
    return update_product(db, product)


def record_movement(
    db: Session,
    *,
    product: Product,
    movement_type: str,
    quantity: int,
    previous_stock: int,
    new_stock: int,
    current_user: User,
    unit_cost=None,
    unit_price=None,
    reference_type=None,
    reference_id=None,
) -> InventoryMovement:
    return create_inventory_movement(
        db,
        InventoryMovement(
            product_id=product.id,
            branch_id=product.branch_id,
            movement_type=movement_type,
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=new_stock,
            unit_cost=unit_cost,
            unit_price=unit_price,
            reference_type=reference_type,
            reference_id=reference_id,
            created_by_user_id=current_user.id,
        ),
    )


def create_manual_movement(db: Session, data: InventoryMovementCreate, current_user: User) -> InventoryMovement:
    ensure_admin(current_user)
    product = get_product_or_404(db, data.product_id)
    previous = product.stock_quantity
    if data.movement_type in {"purchase", "refund"}:
        new_stock = previous + data.quantity
    elif data.movement_type in {"loss"}:
        new_stock = previous - data.quantity
    else:
        new_stock = data.quantity

    if new_stock < 0:
        raise HTTPException(409, "Stock insuficiente")

    product.stock_quantity = new_stock
    product = update_product(db, product)
    return record_movement(
        db,
        product=product,
        movement_type=data.movement_type,
        quantity=data.quantity,
        previous_stock=previous,
        new_stock=new_stock,
        current_user=current_user,
        unit_cost=data.unit_cost,
        unit_price=data.unit_price,
        reference_type=data.reference_type,
        reference_id=data.reference_id,
    )


def get_movements(db: Session, current_user: User, product_id=None, branch_id=None, start_date=None, end_date=None):
    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso")
    if current_user.role == "barber":
        branch_id = current_user.branch_id
    ensure_inventory_access(db, current_user, branch_id)
    return list_inventory_movements(db, product_id, branch_id, start_date, end_date)


def create_sale(db: Session, data: ProductSaleCreate, current_user: User) -> ProductSale:
    if current_user.role not in {"admin", "barber"}:
        raise HTTPException(403, "No tienes permiso")

    product = get_product_or_404(db, data.product_id)
    if not product.is_active:
        raise HTTPException(400, "Producto inactivo")

    branch_id = data.branch_id or product.branch_id or current_user.branch_id
    ensure_inventory_access(db, current_user, branch_id)
    if product.branch_id is not None and product.branch_id != branch_id:
        raise HTTPException(400, "Producto no pertenece a la sucursal seleccionada")

    if data.client_id is not None and not get_client_by_id(db, data.client_id):
        raise HTTPException(404, "Cliente no encontrado")
    if data.payment_id is not None and not get_payment_by_id(db, data.payment_id):
        raise HTTPException(404, "Pago no encontrado")
    if product.stock_quantity < data.quantity:
        raise HTTPException(409, "Stock insuficiente")

    unit_price = data.unit_price if data.unit_price is not None else product.sale_price
    total = Decimal(unit_price) * Decimal(data.quantity)
    cash_session_id = None
    if data.payment_method.value == "cash" and branch_id is not None:
        session = get_open_cash_session_by_branch(db, branch_id)
        if not session:
            raise HTTPException(409, "No hay caja abierta para registrar venta cash")
        cash_session_id = session.id

    previous = product.stock_quantity
    product.stock_quantity = previous - data.quantity
    product = update_product(db, product)
    sale = create_product_sale(
        db,
        ProductSale(
            branch_id=branch_id,
            product_id=product.id,
            client_id=data.client_id,
            payment_id=data.payment_id,
            cash_session_id=cash_session_id,
            quantity=data.quantity,
            unit_price=unit_price,
            total_amount=total,
            sold_by_user_id=current_user.id,
        ),
    )
    record_movement(
        db,
        product=product,
        movement_type="sale",
        quantity=data.quantity,
        previous_stock=previous,
        new_stock=product.stock_quantity,
        current_user=current_user,
        unit_price=unit_price,
        reference_type="product_sale",
        reference_id=sale.id,
    )
    if cash_session_id is not None:
        create_cash_movement(
            db,
            CashMovement(
                cash_session_id=cash_session_id,
                movement_type="income",
                amount=total,
                method="cash",
                description=f"Venta de producto #{sale.id}",
                created_by_user_id=current_user.id,
            ),
        )
    return sale


def get_sales(db: Session, current_user: User, branch_id=None, start_date=None, end_date=None):
    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso")
    if current_user.role == "barber":
        branch_id = current_user.branch_id
    ensure_inventory_access(db, current_user, branch_id)
    return list_product_sales(db, branch_id, start_date, end_date)


def get_low_stock(db: Session, current_user: User, branch_id=None) -> list[Product]:
    if current_user.role == "client":
        raise HTTPException(403, "No tienes permiso")
    if current_user.role == "barber":
        branch_id = current_user.branch_id
    ensure_inventory_access(db, current_user, branch_id)
    return low_stock_products(db, branch_id)


def product_report(db: Session, current_user: User, start_date, end_date) -> dict:
    ensure_admin(current_user)
    top = top_sold_products(db, start_date, end_date)
    by_branch = product_income_by_branch(db, start_date, end_date)
    return {
        "top_products": [
            {
                "product_id": row.product_id,
                "product": row.product,
                "quantity": row.quantity,
                "income": float(row.income or 0),
            }
            for row in top
        ],
        "by_branch": [
            {
                "branch_id": row.branch_id,
                "income": float(row.income or 0),
                "cost": float(row.cost or 0),
                "margin": round(float((row.income or 0) - (row.cost or 0)), 2),
            }
            for row in by_branch
        ],
    }
