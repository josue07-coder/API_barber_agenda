from alembic import op


revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT phone
                FROM clients
                WHERE phone IS NOT NULL
                GROUP BY phone
                HAVING COUNT(*) > 1
            ) THEN
                RAISE EXCEPTION 'No se puede crear uq_clients_phone: existen telefonos duplicados en clients.phone';
            END IF;
        END $$;
        """
    )
    op.create_unique_constraint("uq_clients_phone", "clients", ["phone"])


def downgrade() -> None:
    op.drop_constraint("uq_clients_phone", "clients", type_="unique")
