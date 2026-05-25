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
        sa.Column("canonical_name", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="candidate"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("replacement_entity_id", UUID(as_uuid=True), nullable=True),
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
        sa.Column("created_by", sa.Text, nullable=True),
        sa.Column("updated_by", sa.Text, nullable=True),
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
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("uri", sa.Text, nullable=True),
        sa.Column("version", sa.Text, nullable=True),
        sa.Column("checksum", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
    )
    op.create_index("idx_source_ref_type", "source_ref", ["source_type"])
    op.create_index("idx_source_ref_name", "source_ref", ["name"])

    op.create_table(
        "entity_alias",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("alias", sa.Text, nullable=False),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", sa.Text, nullable=True),
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
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("source_ref_id", UUID(as_uuid=True), nullable=True),
        sa.Column("token_estimate", sa.Integer, nullable=True),
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
        sa.Column("created_by", sa.Text, nullable=True),
        sa.Column("updated_by", sa.Text, nullable=True),
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
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", sa.Text, nullable=True),
    )
    op.create_index("idx_entity_relation_from", "entity_relation", ["from_entity_id"])
    op.create_index("idx_entity_relation_to", "entity_relation", ["to_entity_id"])
    op.create_index("idx_entity_relation_type", "entity_relation", ["relation_type"])

    op.create_table(
        "entity_metadata",
        sa.Column(
            "entity_id",
            UUID(as_uuid=True),
            sa.ForeignKey("entity.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "idx_entity_metadata_gin",
        "entity_metadata",
        ["metadata"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_table("entity_metadata")
    op.drop_table("entity_relation")
    op.drop_table("entity_context")
    op.drop_table("entity_alias")
    op.drop_table("source_ref")
    op.drop_table("entity")
