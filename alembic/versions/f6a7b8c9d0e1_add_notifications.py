from alembic import op
import sqlalchemy as sa


revision = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_type", sa.String(length=30), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("subject", sa.String(length=160), nullable=False),
        sa.Column("message", sa.String(length=1000), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("related_type", sa.String(length=50), nullable=True),
        sa.Column("related_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "channel IN ('email', 'sms', 'whatsapp', 'in_app')",
            name="ck_notifications_channel_allowed",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'cancelled')",
            name="ck_notifications_status_allowed",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_recipient", "notifications", ["recipient_type", "recipient_id"])
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.create_index("ix_notifications_channel", "notifications", ["channel"])
    op.create_index("ix_notifications_scheduled_for", "notifications", ["scheduled_for"])
    op.create_index("ix_notifications_related", "notifications", ["related_type", "related_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_related", table_name="notifications")
    op.drop_index("ix_notifications_scheduled_for", table_name="notifications")
    op.drop_index("ix_notifications_channel", table_name="notifications")
    op.drop_index("ix_notifications_status", table_name="notifications")
    op.drop_index("ix_notifications_recipient", table_name="notifications")
    op.drop_table("notifications")
