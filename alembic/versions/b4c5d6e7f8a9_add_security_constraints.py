from alembic import op


revision = "b4c5d6e7f8a9"
down_revision = "9b1f2c3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_users_role_allowed",
        "users",
        "role IN ('admin', 'barber', 'client')",
    )
    op.create_check_constraint(
        "ck_appointments_status_allowed",
        "appointments",
        "status IN ('agendada', 'confirmada', 'completada', 'cancelada', 'no_show')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_appointments_status_allowed",
        "appointments",
        type_="check",
    )
    op.drop_constraint(
        "ck_users_role_allowed",
        "users",
        type_="check",
    )
