"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "entity",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("canonical_name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="candidate"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("replacement_entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("deprecation_reason", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["replacement_entity_id"], ["entity.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("idx_entity_type", "entity", ["type"])
    op.create_index("idx_entity_status", "entity", ["status"])
    op.create_index("idx_entity_name", "entity", ["canonical_name"])

    op.create_table(
        "source_ref",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("uri", sa.String(2000), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("version", sa.String(100), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_source_ref_uri", "source_ref", ["uri"])

    op.create_table(
        "entity_alias",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("alias", sa.String(500), nullable=False),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_entity_alias_entity_id", "entity_alias", ["entity_id"])
    op.create_index("idx_entity_alias_alias", "entity_alias", ["alias"])
    op.create_index("idx_entity_alias_locale_alias", "entity_alias", ["locale", "alias"])
    op.create_index("idx_entity_alias_active", "entity_alias", ["is_active"])

    op.create_table(
        "entity_context",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("context_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="ko"),
        sa.Column(
            "source_ref_id",
            UUID(as_uuid=True),
            sa.ForeignKey("source_ref.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_entity_context_entity_id", "entity_context", ["entity_id"])
    op.create_index("idx_entity_context_type", "entity_context", ["context_type"])
    op.create_index("idx_entity_context_language", "entity_context", ["language"])

    op.create_table(
        "entity_relation",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "from_entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relation_type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_entity_relation_from", "entity_relation", ["from_entity_id"])
    op.create_index("idx_entity_relation_to", "entity_relation", ["to_entity_id"])
    op.create_index("idx_entity_relation_type", "entity_relation", ["relation_type"])

    op.create_table(
        "entity_metadata",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("meta_type", sa.String(50), nullable=False),
        sa.Column("data", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("entity_id", "meta_type", name="uq_entity_metadata_type"),
    )
    op.create_index(
        "idx_entity_metadata_gin",
        "entity_metadata",
        ["data"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_table("entity_metadata")
    op.drop_table("entity_relation")
    op.drop_table("entity_context")
    op.drop_table("entity_alias")
    op.drop_table("source_ref")
    op.drop_table("entity")
