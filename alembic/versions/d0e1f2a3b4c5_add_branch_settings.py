from alembic import op
import sqlalchemy as sa


revision = "d0e1f2a3b4c5"
down_revision = "c9d0e1f2a3b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branch_settings",
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="America/Santo_Domingo"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="DOP"),
        sa.Column("default_cancel_cutoff_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("default_reschedule_cutoff_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("deposit_required", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("default_deposit_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("default_deposit_percentage", sa.Numeric(5, 2), nullable=True),
        sa.Column("reminder_24h_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("reminder_2h_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("default_cancel_cutoff_hours >= 0", name="ck_branch_settings_cancel_cutoff_nonnegative"),
        sa.CheckConstraint("default_reschedule_cutoff_hours >= 0", name="ck_branch_settings_reschedule_cutoff_nonnegative"),
        sa.CheckConstraint("default_deposit_amount IS NULL OR default_deposit_amount >= 0", name="ck_branch_settings_deposit_amount_nonnegative"),
        sa.CheckConstraint("default_deposit_percentage IS NULL OR (default_deposit_percentage >= 0 AND default_deposit_percentage <= 100)", name="ck_branch_settings_deposit_percentage_range"),
        sa.CheckConstraint("NOT (default_deposit_amount IS NOT NULL AND default_deposit_percentage IS NOT NULL)", name="ck_branch_settings_one_deposit_default"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"]),
        sa.PrimaryKeyConstraint("branch_id"),
    )


def downgrade() -> None:
    op.drop_table("branch_settings")
