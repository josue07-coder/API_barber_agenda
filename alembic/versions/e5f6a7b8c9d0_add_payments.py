from alembic import op
import sqlalchemy as sa


revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "appointments",
        sa.Column(
            "payment_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
    )
    op.create_check_constraint(
        "ck_appointments_payment_status_allowed",
        "appointments",
        "payment_status IN ('pending', 'paid', 'partially_paid', 'refunded', 'failed', 'cancelled')",
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("transaction_reference", sa.String(length=120), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        sa.CheckConstraint(
            "status IN ('pending', 'paid', 'partially_paid', 'refunded', 'failed', 'cancelled')",
            name="ck_payments_status_allowed",
        ),
        sa.CheckConstraint(
            "payment_method IN ('cash', 'card', 'transfer', 'online', 'other')",
            name="ck_payments_method_allowed",
        ),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_appointment_id", "payments", ["appointment_id"])
    op.create_index("ix_payments_client_id", "payments", ["client_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_paid_at", "payments", ["paid_at"])


def downgrade() -> None:
    op.drop_index("ix_payments_paid_at", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_client_id", table_name="payments")
    op.drop_index("ix_payments_appointment_id", table_name="payments")
    op.drop_table("payments")
    op.drop_constraint(
        "ck_appointments_payment_status_allowed",
        "appointments",
        type_="check",
    )
    op.drop_column("appointments", "payment_status")
