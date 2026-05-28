"""add entity_history table

Revision ID: 003
Revises: 002
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("revision_no", sa.Integer, nullable=False),
        sa.Column("snapshot", JSONB, nullable=False),
        sa.Column("changed_fields", JSONB, nullable=True),
        sa.Column("change_type", sa.String(50), nullable=False),
        sa.Column("change_reason", sa.Text, nullable=True),
        sa.Column("changed_by", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("entity_id", "revision_no", name="uq_entity_history_rev"),
    )
    op.create_index("ix_entity_history_entity_id", "entity_history", ["entity_id"])
    op.create_index("ix_entity_history_created_at", "entity_history", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_entity_history_created_at", "entity_history")
    op.drop_index("ix_entity_history_entity_id", "entity_history")
    op.drop_table("entity_history")
