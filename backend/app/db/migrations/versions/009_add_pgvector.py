"""add pgvector extension and context_embedding table

Revision ID: 009
Revises: 008
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "context_embedding",
        sa.Column("context_id", UUID(as_uuid=True), sa.ForeignKey("entity_context.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # HNSW index for cosine similarity (<=>)
    op.execute(
        "CREATE INDEX idx_context_embedding_hnsw "
        "ON context_embedding USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.drop_table("context_embedding")
    op.execute("DROP EXTENSION IF EXISTS vector")
