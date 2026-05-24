from alembic import op
import sqlalchemy as sa


revision = "f3a4b5c6d7e8"
down_revision = "f2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "branch_settings",
        sa.Column("no_show_penalty_points", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "branch_settings",
        sa.Column("no_show_penalty_amount", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "branch_settings",
        sa.Column("late_cancel_penalty_points", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "branch_settings",
        sa.Column("late_cancel_penalty_amount", sa.Numeric(10, 2), nullable=True),
    )
    op.create_check_constraint(
        "ck_branch_settings_no_show_points_nonnegative",
        "branch_settings",
        "no_show_penalty_points >= 0",
    )
    op.create_check_constraint(
        "ck_branch_settings_no_show_amount_nonnegative",
        "branch_settings",
        "no_show_penalty_amount IS NULL OR no_show_penalty_amount >= 0",
    )
    op.create_check_constraint(
        "ck_branch_settings_late_cancel_points_nonnegative",
        "branch_settings",
        "late_cancel_penalty_points >= 0",
    )
    op.create_check_constraint(
        "ck_branch_settings_late_cancel_amount_nonnegative",
        "branch_settings",
        "late_cancel_penalty_amount IS NULL OR late_cancel_penalty_amount >= 0",
    )

    op.create_table(
        "client_penalties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("penalty_type", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("forgiven_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "penalty_type IN ('no_show', 'late_cancel', 'manual')",
            name="ck_client_penalties_type_allowed",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'forgiven', 'paid', 'cancelled')",
            name="ck_client_penalties_status_allowed",
        ),
        sa.CheckConstraint("points >= 0", name="ck_client_penalties_points_nonnegative"),
        sa.CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name="ck_client_penalties_amount_nonnegative",
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["forgiven_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_client_penalties_client_status", "client_penalties", ["client_id", "status"])
    op.create_index("ix_client_penalties_appointment", "client_penalties", ["appointment_id"])
    op.create_index("ix_client_penalties_type", "client_penalties", ["penalty_type"])
    op.create_index("ix_client_penalties_created_at", "client_penalties", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_client_penalties_created_at", table_name="client_penalties")
    op.drop_index("ix_client_penalties_type", table_name="client_penalties")
    op.drop_index("ix_client_penalties_appointment", table_name="client_penalties")
    op.drop_index("ix_client_penalties_client_status", table_name="client_penalties")
    op.drop_table("client_penalties")
    op.drop_constraint("ck_branch_settings_late_cancel_amount_nonnegative", "branch_settings", type_="check")
    op.drop_constraint("ck_branch_settings_late_cancel_points_nonnegative", "branch_settings", type_="check")
    op.drop_constraint("ck_branch_settings_no_show_amount_nonnegative", "branch_settings", type_="check")
    op.drop_constraint("ck_branch_settings_no_show_points_nonnegative", "branch_settings", type_="check")
    op.drop_column("branch_settings", "late_cancel_penalty_amount")
    op.drop_column("branch_settings", "late_cancel_penalty_points")
    op.drop_column("branch_settings", "no_show_penalty_amount")
    op.drop_column("branch_settings", "no_show_penalty_points")
