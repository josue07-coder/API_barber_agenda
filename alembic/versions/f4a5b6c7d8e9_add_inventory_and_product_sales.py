from alembic import op
import sqlalchemy as sa


revision = "f4a5b6c7d8e9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("barcode", sa.String(length=80), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("brand", sa.String(length=80), nullable=True),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("sale_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False),
        sa.Column("min_stock_alert", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("cost_price >= 0", name="ck_products_cost_price_nonnegative"),
        sa.CheckConstraint("sale_price >= 0", name="ck_products_sale_price_nonnegative"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_products_stock_nonnegative"),
        sa.CheckConstraint("min_stock_alert >= 0", name="ck_products_min_stock_nonnegative"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_branch", "products", ["branch_id"])
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_barcode", "products", ["barcode"])

    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("previous_stock", sa.Integer(), nullable=False),
        sa.Column("new_stock", sa.Integer(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("reference_type", sa.String(length=50), nullable=True),
        sa.Column("reference_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "movement_type IN ('purchase', 'sale', 'adjustment', 'loss', 'refund')",
            name="ck_inventory_movements_type_allowed",
        ),
        sa.CheckConstraint("quantity > 0", name="ck_inventory_movements_quantity_positive"),
        sa.CheckConstraint("previous_stock >= 0", name="ck_inventory_movements_previous_stock_nonnegative"),
        sa.CheckConstraint("new_stock >= 0", name="ck_inventory_movements_new_stock_nonnegative"),
        sa.CheckConstraint("unit_cost IS NULL OR unit_cost >= 0", name="ck_inventory_movements_unit_cost_nonnegative"),
        sa.CheckConstraint("unit_price IS NULL OR unit_price >= 0", name="ck_inventory_movements_unit_price_nonnegative"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inventory_movements_product", "inventory_movements", ["product_id"])
    op.create_index("ix_inventory_movements_branch", "inventory_movements", ["branch_id"])
    op.create_index("ix_inventory_movements_created_at", "inventory_movements", ["created_at"])
    op.create_index("ix_inventory_movements_reference", "inventory_movements", ["reference_type", "reference_id"])

    op.create_table(
        "product_sales",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=True),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("cash_session_id", sa.Integer(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("sold_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("quantity > 0", name="ck_product_sales_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_product_sales_unit_price_nonnegative"),
        sa.CheckConstraint("total_amount >= 0", name="ck_product_sales_total_amount_nonnegative"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["cash_session_id"], ["cash_sessions.id"]),
        sa.ForeignKeyConstraint(["sold_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_product_sales_branch", "product_sales", ["branch_id"])
    op.create_index("ix_product_sales_product", "product_sales", ["product_id"])
    op.create_index("ix_product_sales_client", "product_sales", ["client_id"])
    op.create_index("ix_product_sales_created_at", "product_sales", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_product_sales_created_at", table_name="product_sales")
    op.drop_index("ix_product_sales_client", table_name="product_sales")
    op.drop_index("ix_product_sales_product", table_name="product_sales")
    op.drop_index("ix_product_sales_branch", table_name="product_sales")
    op.drop_table("product_sales")
    op.drop_index("ix_inventory_movements_reference", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_created_at", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_branch", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_product", table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_index("ix_products_barcode", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_index("ix_products_branch", table_name="products")
    op.drop_table("products")
