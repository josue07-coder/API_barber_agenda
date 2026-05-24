from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Numeric
from sqlalchemy import func
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProductSale(Base):
    __tablename__ = "product_sales"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_product_sales_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_product_sales_unit_price_nonnegative"),
        CheckConstraint("total_amount >= 0", name="ck_product_sales_total_amount_nonnegative"),
        Index("ix_product_sales_branch", "branch_id"),
        Index("ix_product_sales_product", "product_id"),
        Index("ix_product_sales_client", "client_id"),
        Index("ix_product_sales_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    cash_session_id = Column(Integer, ForeignKey("cash_sessions.id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    sold_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    branch = relationship("Branch")
    product = relationship("Product")
    client = relationship("Client")
    payment = relationship("Payment")
    cash_session = relationship("CashSession")
    sold_by = relationship("User")
