from alembic import op
import sqlalchemy as sa


revision = "f2a3b4c5d6e7"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "barber_commission_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barber_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("commission_type", sa.String(length=20), nullable=False),
        sa.Column("commission_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "commission_type IN ('percentage', 'fixed')",
            name="ck_commission_rules_type_allowed",
        ),
        sa.CheckConstraint(
            "commission_value >= 0",
            name="ck_commission_rules_value_nonnegative",
        ),
        sa.ForeignKeyConstraint(["barber_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commission_rules_barber", "barber_commission_rules", ["barber_id"])
    op.create_index("ix_commission_rules_branch", "barber_commission_rules", ["branch_id"])
    op.create_index("ix_commission_rules_service", "barber_commission_rules", ["service_id"])

    op.create_table(
        "barber_commissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("barber_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=True),
        sa.Column("service_id", sa.Integer(), nullable=False),
        sa.Column("base_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("commission_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'paid', 'cancelled')",
            name="ck_barber_commissions_status_allowed",
        ),
        sa.CheckConstraint("base_amount >= 0", name="ck_barber_commissions_base_nonnegative"),
        sa.CheckConstraint("commission_amount >= 0", name="ck_barber_commissions_amount_nonnegative"),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"]),
        sa.ForeignKeyConstraint(["barber_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_id", name="uq_barber_commissions_payment"),
    )
    op.create_index("ix_barber_commissions_barber", "barber_commissions", ["barber_id"])
    op.create_index("ix_barber_commissions_branch", "barber_commissions", ["branch_id"])
    op.create_index("ix_barber_commissions_status", "barber_commissions", ["status"])
    op.create_index("ix_barber_commissions_payment", "barber_commissions", ["payment_id"])


def downgrade() -> None:
    op.drop_index("ix_barber_commissions_payment", table_name="barber_commissions")
    op.drop_index("ix_barber_commissions_status", table_name="barber_commissions")
    op.drop_index("ix_barber_commissions_branch", table_name="barber_commissions")
    op.drop_index("ix_barber_commissions_barber", table_name="barber_commissions")
    op.drop_table("barber_commissions")
    op.drop_index("ix_commission_rules_service", table_name="barber_commission_rules")
    op.drop_index("ix_commission_rules_branch", table_name="barber_commission_rules")
    op.drop_index("ix_commission_rules_barber", table_name="barber_commission_rules")
    op.drop_table("barber_commission_rules")
