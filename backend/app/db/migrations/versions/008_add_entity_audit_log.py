"""add entity_audit_log table

Revision ID: 008
Revises: 007
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor", sa.String(200), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(200), nullable=False),
        sa.Column("before_snapshot", JSONB, nullable=True),
        sa.Column("after_snapshot", JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("idx_audit_log_actor", "entity_audit_log", ["actor"])
    op.create_index("idx_audit_log_action", "entity_audit_log", ["action"])
    op.create_index("idx_audit_log_target_id", "entity_audit_log", ["target_id"])
    op.create_index("idx_audit_log_created_at", "entity_audit_log", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_audit_log_created_at", table_name="entity_audit_log")
    op.drop_index("idx_audit_log_target_id", table_name="entity_audit_log")
    op.drop_index("idx_audit_log_action", table_name="entity_audit_log")
    op.drop_index("idx_audit_log_actor", table_name="entity_audit_log")
    op.drop_table("entity_audit_log")
