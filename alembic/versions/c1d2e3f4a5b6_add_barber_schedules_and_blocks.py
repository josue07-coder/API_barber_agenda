from alembic import op
import sqlalchemy as sa


revision = "c1d2e3f4a5b6"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "barber_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barber_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_start_time", sa.Time(), nullable=True),
        sa.Column("break_end_time", sa.Time(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["barber_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_barber_schedules_weekday"),
        sa.CheckConstraint("start_time < end_time", name="ck_barber_schedules_time_range"),
        sa.CheckConstraint(
            "(break_start_time IS NULL AND break_end_time IS NULL) OR "
            "(break_start_time IS NOT NULL AND break_end_time IS NOT NULL AND "
            "break_start_time < break_end_time AND "
            "break_start_time >= start_time AND break_end_time <= end_time)",
            name="ck_barber_schedules_break_range",
        ),
    )
    op.create_index(
        "ix_barber_schedules_barber_weekday",
        "barber_schedules",
        ["barber_id", "weekday"],
    )

    op.create_table(
        "barber_time_blocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barber_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("is_full_day", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["barber_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "(is_full_day = true AND start_time IS NULL AND end_time IS NULL) OR "
            "(is_full_day = false AND start_time IS NOT NULL AND end_time IS NOT NULL AND start_time < end_time)",
            name="ck_barber_time_blocks_range",
        ),
    )
    op.create_index(
        "ix_barber_time_blocks_barber_date",
        "barber_time_blocks",
        ["barber_id", "date"],
    )
    op.create_index("ix_barber_time_blocks_date", "barber_time_blocks", ["date"])

    op.execute(
        """
        ALTER TABLE barber_schedules
        ADD CONSTRAINT ex_barber_schedules_active_overlap
        EXCLUDE USING gist (
            barber_id WITH =,
            weekday WITH =,
            tsrange(date '2000-01-01' + start_time, date '2000-01-01' + end_time, '[)') WITH &&
        )
        WHERE (is_active)
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE barber_schedules "
        "DROP CONSTRAINT IF EXISTS ex_barber_schedules_active_overlap"
    )
    op.drop_index("ix_barber_time_blocks_date", table_name="barber_time_blocks")
    op.drop_index("ix_barber_time_blocks_barber_date", table_name="barber_time_blocks")
    op.drop_table("barber_time_blocks")
    op.drop_index("ix_barber_schedules_barber_weekday", table_name="barber_schedules")
    op.drop_table("barber_schedules")
