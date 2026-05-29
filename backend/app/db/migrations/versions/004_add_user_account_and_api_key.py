"""add user_account and api_key tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_account",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
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
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["user_account.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("email", name="uq_user_account_email"),
    )
    op.create_index("idx_user_account_email", "user_account", ["email"])
    op.create_index("idx_user_account_role", "user_account", ["role"])

    op.create_table(
        "api_key",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("key_hash", sa.Text, nullable=False),
        sa.Column("scopes", ARRAY(sa.String(50)), nullable=False, server_default="{}"),
        sa.Column("project_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"], ["user_account.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("idx_api_key_key_hash", "api_key", ["key_hash"])
    op.create_index("idx_api_key_project_id", "api_key", ["project_id"])


def downgrade() -> None:
    op.drop_table("api_key")
    op.drop_table("user_account")
