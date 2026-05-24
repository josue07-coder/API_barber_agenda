from alembic import op
import sqlalchemy as sa


revision = "d4e5f6a7b8c9"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("appointments", sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("appointments", sa.Column("cancelled_by_user_id", sa.Integer(), nullable=True))
    op.add_column("appointments", sa.Column("cancellation_reason", sa.String(length=255), nullable=True))
    op.add_column(
        "appointments",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
    )
    op.create_foreign_key(
        "fk_appointments_cancelled_by_user_id_users",
        "appointments",
        "users",
        ["cancelled_by_user_id"],
        ["id"],
    )

    op.create_table(
        "appointment_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_appointment_history_appointment_id",
        "appointment_history",
        ["appointment_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_appointment_history_appointment_id", table_name="appointment_history")
    op.drop_table("appointment_history")
    op.drop_constraint(
        "fk_appointments_cancelled_by_user_id_users",
        "appointments",
        type_="foreignkey",
    )
    op.drop_column("appointments", "updated_at")
    op.drop_column("appointments", "cancellation_reason")
    op.drop_column("appointments", "cancelled_by_user_id")
    op.drop_column("appointments", "cancelled_at")
