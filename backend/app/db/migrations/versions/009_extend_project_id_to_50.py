"""extend project_id columns to String(50) and expand allowed charset

Revision ID: 009
Revises: 008
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("project", "id", type_=sa.String(50), existing_type=sa.String(20), existing_nullable=False)
    op.alter_column("project_member", "project_id", type_=sa.String(50), existing_type=sa.String(20), existing_nullable=False)
    op.alter_column("entity", "project_id", type_=sa.String(50), existing_type=sa.String(20), existing_nullable=True)
    op.alter_column("entity_context", "project_id", type_=sa.String(50), existing_type=sa.String(20), existing_nullable=True)
    op.alter_column("entity_relation", "project_id", type_=sa.String(50), existing_type=sa.String(20), existing_nullable=True)


def downgrade() -> None:
    op.alter_column("entity_relation", "project_id", type_=sa.String(20), existing_type=sa.String(50), existing_nullable=True)
    op.alter_column("entity_context", "project_id", type_=sa.String(20), existing_type=sa.String(50), existing_nullable=True)
    op.alter_column("entity", "project_id", type_=sa.String(20), existing_type=sa.String(50), existing_nullable=True)
    op.alter_column("project_member", "project_id", type_=sa.String(20), existing_type=sa.String(50), existing_nullable=False)
    op.alter_column("project", "id", type_=sa.String(20), existing_type=sa.String(50), existing_nullable=False)
