from alembic import op
import sqlalchemy as sa


revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("client_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_client_id", "users", ["client_id"])
    op.create_unique_constraint("uq_users_client_id", "users", ["client_id"])
    op.create_foreign_key(
        "fk_users_client_id_clients",
        "users",
        "clients",
        ["client_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_client_id_clients", "users", type_="foreignkey")
    op.drop_constraint("uq_users_client_id", "users", type_="unique")
    op.drop_index("ix_users_client_id", table_name="users")
    op.drop_column("users", "client_id")
