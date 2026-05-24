from alembic import op


revision = "9b1f2c3d4e5f"
down_revision = "7dead717d170"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_appointments_user_date_start_time",
        "appointments",
        ["user_id", "date", "start_time"],
    )
    op.create_index(
        "ix_appointments_client_date",
        "appointments",
        ["client_id", "date"],
    )
    op.create_index("ix_appointments_status", "appointments", ["status"])
    op.create_index("ix_appointments_date", "appointments", ["date"])

    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    op.execute(
        """
        CREATE UNIQUE INDEX uq_appointments_active_user_date_start_time
        ON appointments (user_id, date, start_time)
        WHERE status NOT IN ('cancelada', 'no_show')
        """
    )
    op.execute(
        """
        ALTER TABLE appointments
        ADD CONSTRAINT ex_appointments_active_user_time_overlap
        EXCLUDE USING gist (
            user_id WITH =,
            tsrange(date + start_time, date + end_time, '[)') WITH &&
        )
        WHERE (status NOT IN ('cancelada', 'no_show'))
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE appointments "
        "DROP CONSTRAINT IF EXISTS ex_appointments_active_user_time_overlap"
    )
    op.execute("DROP INDEX IF EXISTS uq_appointments_active_user_date_start_time")
    op.drop_index("ix_appointments_date", table_name="appointments")
    op.drop_index("ix_appointments_status", table_name="appointments")
    op.drop_index("ix_appointments_client_date", table_name="appointments")
    op.drop_index("ix_appointments_user_date_start_time", table_name="appointments")
