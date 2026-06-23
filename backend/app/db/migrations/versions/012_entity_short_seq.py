"""add entity.short_seq for short identifier PROJECT_ID-TYPE-N

Revision ID: 012
Revises: 011
Create Date: 2026-06-23
"""
from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("entity", sa.Column("short_seq", sa.Integer(), nullable=True))
    # Backfill existing scoped entities: per (project_id, type), number by
    # created_at then id (deterministic, reproducible).
    op.execute(
        """
        UPDATE entity AS e
        SET short_seq = numbered.rn
        FROM (
            SELECT id,
                   ROW_NUMBER() OVER (
                       PARTITION BY project_id, type
                       ORDER BY created_at, id
                   ) AS rn
            FROM entity
            WHERE project_id IS NOT NULL
        ) AS numbered
        WHERE e.id = numbered.id
        """
    )
    op.create_unique_constraint(
        "uq_entity_short_seq", "entity", ["project_id", "type", "short_seq"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_entity_short_seq", "entity", type_="unique")
    op.drop_column("entity", "short_seq")
