from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("cost_price >= 0", name="ck_products_cost_price_nonnegative"),
        CheckConstraint("sale_price >= 0", name="ck_products_sale_price_nonnegative"),
        CheckConstraint("stock_quantity >= 0", name="ck_products_stock_nonnegative"),
        CheckConstraint("min_stock_alert >= 0", name="ck_products_min_stock_nonnegative"),
        Index("ix_products_branch", "branch_id"),
        Index("ix_products_sku", "sku", unique=True),
        Index("ix_products_barcode", "barcode"),
    )

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    name = Column(String(120), nullable=False)
    description = Column(String(500), nullable=True)
    sku = Column(String(80), nullable=False, unique=True)
    barcode = Column(String(80), nullable=True)
    category = Column(String(80), nullable=True)
    brand = Column(String(80), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    min_stock_alert = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    branch = relationship("Branch")
