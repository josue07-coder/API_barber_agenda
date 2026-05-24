from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.product_sale import ProductSale


def create_product(db: Session, product: Product) -> Product:
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product) -> Product:
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def get_product_by_id(db: Session, product_id: int) -> Product | None:
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_sku(db: Session, sku: str) -> Product | None:
    return db.query(Product).filter(Product.sku == sku).first()


def list_products(db: Session, branch_id: int | None = None, include_inactive: bool = False) -> list[Product]:
    query = db.query(Product)
    if branch_id is not None:
        query = query.filter((Product.branch_id == branch_id) | (Product.branch_id.is_(None)))
    if not include_inactive:
        query = query.filter(Product.is_active == True)
    return query.order_by(Product.name).all()


def low_stock_products(db: Session, branch_id: int | None = None) -> list[Product]:
    query = db.query(Product).filter(Product.is_active == True, Product.stock_quantity <= Product.min_stock_alert)
    if branch_id is not None:
        query = query.filter((Product.branch_id == branch_id) | (Product.branch_id.is_(None)))
    return query.order_by(Product.stock_quantity, Product.name).all()


def create_inventory_movement(db: Session, movement: InventoryMovement) -> InventoryMovement:
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def list_inventory_movements(
    db: Session,
    product_id: int | None = None,
    branch_id: int | None = None,
    start_date=None,
    end_date=None,
) -> list[InventoryMovement]:
    query = db.query(InventoryMovement)
    if product_id is not None:
        query = query.filter(InventoryMovement.product_id == product_id)
    if branch_id is not None:
        query = query.filter(InventoryMovement.branch_id == branch_id)
    if start_date is not None:
        query = query.filter(func.date(InventoryMovement.created_at) >= start_date)
    if end_date is not None:
        query = query.filter(func.date(InventoryMovement.created_at) <= end_date)
    return query.order_by(InventoryMovement.created_at.desc(), InventoryMovement.id.desc()).all()


def create_product_sale(db: Session, sale: ProductSale) -> ProductSale:
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale


def list_product_sales(db: Session, branch_id: int | None = None, start_date=None, end_date=None) -> list[ProductSale]:
    query = db.query(ProductSale)
    if branch_id is not None:
        query = query.filter(ProductSale.branch_id == branch_id)
    if start_date is not None:
        query = query.filter(func.date(ProductSale.created_at) >= start_date)
    if end_date is not None:
        query = query.filter(func.date(ProductSale.created_at) <= end_date)
    return query.order_by(ProductSale.created_at.desc(), ProductSale.id.desc()).all()


def top_sold_products(db: Session, start_date, end_date):
    return (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product"),
            func.coalesce(func.sum(ProductSale.quantity), 0).label("quantity"),
            func.coalesce(func.sum(ProductSale.total_amount), 0).label("income"),
        )
        .join(ProductSale, ProductSale.product_id == Product.id)
        .filter(func.date(ProductSale.created_at).between(start_date, end_date))
        .group_by(Product.id, Product.name)
        .order_by(func.sum(ProductSale.quantity).desc())
        .all()
    )


def product_income_by_branch(db: Session, start_date, end_date):
    return (
        db.query(
            ProductSale.branch_id.label("branch_id"),
            func.coalesce(func.sum(ProductSale.total_amount), 0).label("income"),
            func.coalesce(func.sum(ProductSale.quantity * Product.cost_price), 0).label("cost"),
        )
        .join(Product, Product.id == ProductSale.product_id)
        .filter(func.date(ProductSale.created_at).between(start_date, end_date))
        .group_by(ProductSale.branch_id)
        .all()
    )
