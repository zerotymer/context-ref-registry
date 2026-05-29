"""add project table

Revision ID: 005
Revises: 004
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.String(20), primary_key=True),
        sa.Column("alias", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
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
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["user_account.id"]),
    )
    op.create_index("idx_project_is_active", "project", ["is_active"])


def downgrade() -> None:
    op.drop_table("project")
