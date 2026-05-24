from alembic import op
import sqlalchemy as sa


revision = "e1f2a3b4c5d6"
down_revision = "d0e1f2a3b4c5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cash_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("opened_by_user_id", sa.Integer(), nullable=False),
        sa.Column("closed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("opening_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("closing_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("expected_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("difference_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.CheckConstraint("status IN ('open', 'closed')", name="ck_cash_sessions_status_allowed"),
        sa.CheckConstraint("opening_amount >= 0", name="ck_cash_sessions_opening_amount_nonnegative"),
        sa.CheckConstraint("closing_amount IS NULL OR closing_amount >= 0", name="ck_cash_sessions_closing_amount_nonnegative"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["opened_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_sessions_branch_status", "cash_sessions", ["branch_id", "status"])
    op.create_index(
        "uq_cash_sessions_open_branch",
        "cash_sessions",
        ["branch_id"],
        unique=True,
        postgresql_where=sa.text("status = 'open'"),
    )

    op.create_table(
        "cash_movements",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cash_session_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=True),
        sa.Column("movement_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("movement_type IN ('income', 'expense', 'adjustment', 'refund')", name="ck_cash_movements_type_allowed"),
        sa.CheckConstraint("method IN ('cash', 'card', 'transfer', 'online', 'other')", name="ck_cash_movements_method_allowed"),
        sa.CheckConstraint("amount > 0", name="ck_cash_movements_amount_positive"),
        sa.ForeignKeyConstraint(["cash_session_id"], ["cash_sessions.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cash_movements_session", "cash_movements", ["cash_session_id"])
    op.create_index("ix_cash_movements_payment", "cash_movements", ["payment_id"])
    op.create_index(
        "uq_cash_movements_payment_type",
        "cash_movements",
        ["payment_id", "movement_type"],
        unique=True,
        postgresql_where=sa.text("payment_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_cash_movements_payment_type", table_name="cash_movements")
    op.drop_index("ix_cash_movements_payment", table_name="cash_movements")
    op.drop_index("ix_cash_movements_session", table_name="cash_movements")
    op.drop_table("cash_movements")
    op.drop_index("uq_cash_sessions_open_branch", table_name="cash_sessions")
    op.drop_index("ix_cash_sessions_branch_status", table_name="cash_sessions")
    op.drop_table("cash_sessions")
