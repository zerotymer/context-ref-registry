"""rename user_account.email to login_id, add must_change_password

Revision ID: 011
Revises: 010
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("user_account", "email", new_column_name="login_id")
    op.add_column(
        "user_account",
        sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("user_account", "must_change_password")
    op.alter_column("user_account", "login_id", new_column_name="email")
