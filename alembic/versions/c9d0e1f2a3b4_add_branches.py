from alembic import op
import sqlalchemy as sa


revision = "c9d0e1f2a3b4"
down_revision = "b8c9d0e1f2a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_branches_name"),
    )
    op.create_index("ix_branches_id", "branches", ["id"])

    op.add_column("users", sa.Column("branch_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_branch_id", "users", ["branch_id"])
    op.create_foreign_key(
        "fk_users_branch_id_branches",
        "users",
        "branches",
        ["branch_id"],
        ["id"],
    )

    op.add_column("services", sa.Column("branch_id", sa.Integer(), nullable=True))
    op.create_index("ix_services_branch_id", "services", ["branch_id"])
    op.create_foreign_key(
        "fk_services_branch_id_branches",
        "services",
        "branches",
        ["branch_id"],
        ["id"],
    )

    op.add_column("appointments", sa.Column("branch_id", sa.Integer(), nullable=True))
    op.create_index("ix_appointments_branch_id", "appointments", ["branch_id"])
    op.create_foreign_key(
        "fk_appointments_branch_id_branches",
        "appointments",
        "branches",
        ["branch_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_appointments_branch_id_branches", "appointments", type_="foreignkey")
    op.drop_index("ix_appointments_branch_id", table_name="appointments")
    op.drop_column("appointments", "branch_id")

    op.drop_constraint("fk_services_branch_id_branches", "services", type_="foreignkey")
    op.drop_index("ix_services_branch_id", table_name="services")
    op.drop_column("services", "branch_id")

    op.drop_constraint("fk_users_branch_id_branches", "users", type_="foreignkey")
    op.drop_index("ix_users_branch_id", table_name="users")
    op.drop_column("users", "branch_id")

    op.drop_index("ix_branches_id", table_name="branches")
    op.drop_table("branches")
