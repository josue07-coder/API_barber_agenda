from alembic import op
import sqlalchemy as sa


revision = "7dead717d170"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "users",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column(
        "clients",
        sa.Column("notes", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "services",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column(
        "services",
        "price",
        existing_type=sa.Float(),
        type_=sa.Numeric(10, 2),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "services",
        "price",
        existing_type=sa.Numeric(10, 2),
        type_=sa.Float(),
        existing_nullable=False,
    )
    op.drop_column("services", "is_active")
    op.drop_column("clients", "is_active")
    op.drop_column("clients", "notes")
    op.drop_column("users", "created_at")
    op.drop_column("users", "is_active")
