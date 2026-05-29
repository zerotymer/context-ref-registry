"""add project_member table

Revision ID: 006
Revises: 005
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_member",
        sa.Column("project_id", sa.String(20), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("created_by", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user_account.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user_account.id"]),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )
    op.create_index("idx_project_member_user_id", "project_member", ["user_id"])
    op.create_index("idx_project_member_project_id", "project_member", ["project_id"])


def downgrade() -> None:
    op.drop_table("project_member")
