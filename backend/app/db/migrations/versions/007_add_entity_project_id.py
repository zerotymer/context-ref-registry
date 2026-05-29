"""add project_id to entity, entity_context, entity_relation

Revision ID: 007
Revises: 006
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("entity", sa.Column("project_id", sa.String(20), nullable=True))
    op.add_column("entity_context", sa.Column("project_id", sa.String(20), nullable=True))
    op.add_column("entity_relation", sa.Column("project_id", sa.String(20), nullable=True))

    op.create_foreign_key(
        "fk_entity_project_id", "entity", "project", ["project_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_entity_context_project_id", "entity_context", "project", ["project_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_entity_relation_project_id", "entity_relation", "project", ["project_id"], ["id"]
    )

    op.create_index("idx_entity_project_id", "entity", ["project_id"])
    op.create_index("idx_entity_context_project_id", "entity_context", ["project_id"])
    op.create_index("idx_entity_relation_project_id", "entity_relation", ["project_id"])


def downgrade() -> None:
    op.drop_index("idx_entity_project_id", table_name="entity")
    op.drop_index("idx_entity_context_project_id", table_name="entity_context")
    op.drop_index("idx_entity_relation_project_id", table_name="entity_relation")

    op.drop_constraint("fk_entity_project_id", "entity", type_="foreignkey")
    op.drop_constraint("fk_entity_context_project_id", "entity_context", type_="foreignkey")
    op.drop_constraint("fk_entity_relation_project_id", "entity_relation", type_="foreignkey")

    op.drop_column("entity", "project_id")
    op.drop_column("entity_context", "project_id")
    op.drop_column("entity_relation", "project_id")
