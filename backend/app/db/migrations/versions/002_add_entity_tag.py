"""add entity_tag table

Revision ID: 002
Revises: 001
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity_tag",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tag", sa.String(200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("entity_id", "tag", name="uq_entity_tag"),
    )
    op.create_index("ix_entity_tag_entity_id", "entity_tag", ["entity_id"])
    op.create_index("ix_entity_tag_tag", "entity_tag", ["tag"])


def downgrade() -> None:
    op.drop_index("ix_entity_tag_tag", "entity_tag")
    op.drop_index("ix_entity_tag_entity_id", "entity_tag")
    op.drop_table("entity_tag")
