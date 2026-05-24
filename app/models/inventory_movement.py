from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    __table_args__ = (
        CheckConstraint(
            "movement_type IN ('purchase', 'sale', 'adjustment', 'loss', 'refund')",
            name="ck_inventory_movements_type_allowed",
        ),
        CheckConstraint("quantity > 0", name="ck_inventory_movements_quantity_positive"),
        CheckConstraint("previous_stock >= 0", name="ck_inventory_movements_previous_stock_nonnegative"),
        CheckConstraint("new_stock >= 0", name="ck_inventory_movements_new_stock_nonnegative"),
        CheckConstraint("unit_cost IS NULL OR unit_cost >= 0", name="ck_inventory_movements_unit_cost_nonnegative"),
        CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="ck_inventory_movements_unit_price_nonnegative"),
        Index("ix_inventory_movements_product", "product_id"),
        Index("ix_inventory_movements_branch", "branch_id"),
        Index("ix_inventory_movements_created_at", "created_at"),
        Index("ix_inventory_movements_reference", "reference_type", "reference_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    movement_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=True)
    reference_type = Column(String(50), nullable=True)
    reference_id = Column(Integer, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    branch = relationship("Branch")
    created_by = relationship("User")
