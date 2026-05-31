"""change api_key.project_id from UUID to String(50) with FK to project

Revision ID: 010
Revises: 009
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing UUID column (no FK constraint was defined)
    op.drop_column("api_key", "project_id")
    # Add new String(50) column with FK
    op.add_column(
        "api_key",
        sa.Column(
            "project_id",
            sa.String(50),
            sa.ForeignKey("project.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("api_key", "project_id")
    op.add_column(
        "api_key",
        sa.Column("project_id", UUID(as_uuid=True), nullable=True),
    )
