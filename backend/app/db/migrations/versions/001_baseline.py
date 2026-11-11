"""baseline — SQLite schema (squashed PostgreSQL revisions 001~012)

Revision ID: 001
Revises: 
Create Date: 2026-11-11 09:02:12.256681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.domain.models import UtcDateTime


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('entity_audit_log',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('actor', sa.String(length=200), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('target_type', sa.String(length=50), nullable=False),
    sa.Column('target_id', sa.String(length=200), nullable=False),
    sa.Column('before_snapshot', sa.JSON(), nullable=True),
    sa.Column('after_snapshot', sa.JSON(), nullable=True),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('entity_audit_log', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entity_audit_log_action'), ['action'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_audit_log_actor'), ['actor'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_audit_log_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_audit_log_target_id'), ['target_id'], unique=False)

    op.create_table('project',
    sa.Column('id', sa.String(length=50), nullable=False),
    sa.Column('alias', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('source_ref',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('uri', sa.String(length=2000), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('version', sa.String(length=100), nullable=True),
    sa.Column('retrieved_at', UtcDateTime(), nullable=True),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('api_key',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('key_hash', sa.Text(), nullable=False),
    sa.Column('project_id', sa.String(length=50), nullable=False),
    sa.Column('scope', sa.String(length=10), nullable=False),
    sa.Column('expires_at', UtcDateTime(), nullable=True),
    sa.Column('last_used_at', UtcDateTime(), nullable=True),
    sa.Column('revoked_at', UtcDateTime(), nullable=True),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('key_hash')
    )
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_api_key_project_id'), ['project_id'], unique=False)

    op.create_table('entity',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('canonical_name', sa.String(length=500), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('replacement_entity_id', sa.Uuid(), nullable=True),
    sa.Column('deprecation_reason', sa.Text(), nullable=True),
    sa.Column('project_id', sa.String(length=50), nullable=True),
    sa.Column('short_seq', sa.Integer(), nullable=True),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['replacement_entity_id'], ['entity.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'type', 'short_seq', name='uq_entity_short_seq')
    )
    with op.batch_alter_table('entity', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entity_project_id'), ['project_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_type'), ['type'], unique=False)

    op.create_table('entity_alias',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=False),
    sa.Column('locale', sa.String(length=10), nullable=False),
    sa.Column('alias', sa.String(length=500), nullable=False),
    sa.Column('is_primary', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('entity_alias', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entity_alias_alias'), ['alias'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_alias_locale'), ['locale'], unique=False)

    op.create_table('entity_context',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=False),
    sa.Column('context_type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('language', sa.String(length=10), nullable=False),
    sa.Column('source_ref_id', sa.Uuid(), nullable=True),
    sa.Column('project_id', sa.String(length=50), nullable=True),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['source_ref_id'], ['source_ref.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('entity_context', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entity_context_context_type'), ['context_type'], unique=False)

    op.create_table('entity_history',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=False),
    sa.Column('revision_no', sa.Integer(), nullable=False),
    sa.Column('snapshot', sa.JSON(), nullable=False),
    sa.Column('changed_fields', sa.JSON(), nullable=True),
    sa.Column('change_type', sa.String(length=50), nullable=False),
    sa.Column('change_reason', sa.Text(), nullable=True),
    sa.Column('changed_by', sa.String(length=200), nullable=True),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('entity_id', 'revision_no', name='uq_entity_history_rev')
    )
    with op.batch_alter_table('entity_history', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entity_history_created_at'), ['created_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_history_entity_id'), ['entity_id'], unique=False)

    op.create_table('entity_metadata',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=False),
    sa.Column('meta_type', sa.String(length=50), nullable=False),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('entity_id', 'meta_type', name='uq_entity_metadata_type')
    )
    op.create_table('entity_relation',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('from_entity_id', sa.Uuid(), nullable=False),
    sa.Column('to_entity_id', sa.Uuid(), nullable=False),
    sa.Column('relation_type', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=False),
    sa.Column('project_id', sa.String(length=50), nullable=True),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['from_entity_id'], ['entity.id'], ),
    sa.ForeignKeyConstraint(['project_id'], ['project.id'], ),
    sa.ForeignKeyConstraint(['to_entity_id'], ['entity.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('entity_relation', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entity_relation_from_entity_id'), ['from_entity_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_relation_to_entity_id'), ['to_entity_id'], unique=False)

    op.create_table('entity_tag',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('entity_id', sa.Uuid(), nullable=False),
    sa.Column('tag', sa.String(length=200), nullable=False),
    sa.Column('created_at', UtcDateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['entity.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('entity_id', 'tag', name='uq_entity_tag')
    )
    with op.batch_alter_table('entity_tag', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_entity_tag_entity_id'), ['entity_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_entity_tag_tag'), ['tag'], unique=False)



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('entity_tag', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entity_tag_tag'))
        batch_op.drop_index(batch_op.f('ix_entity_tag_entity_id'))

    op.drop_table('entity_tag')
    with op.batch_alter_table('entity_relation', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entity_relation_to_entity_id'))
        batch_op.drop_index(batch_op.f('ix_entity_relation_from_entity_id'))

    op.drop_table('entity_relation')
    op.drop_table('entity_metadata')
    with op.batch_alter_table('entity_history', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entity_history_entity_id'))
        batch_op.drop_index(batch_op.f('ix_entity_history_created_at'))

    op.drop_table('entity_history')
    with op.batch_alter_table('entity_context', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entity_context_context_type'))

    op.drop_table('entity_context')
    with op.batch_alter_table('entity_alias', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entity_alias_locale'))
        batch_op.drop_index(batch_op.f('ix_entity_alias_alias'))

    op.drop_table('entity_alias')
    with op.batch_alter_table('entity', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entity_type'))
        batch_op.drop_index(batch_op.f('ix_entity_status'))
        batch_op.drop_index(batch_op.f('ix_entity_project_id'))

    op.drop_table('entity')
    with op.batch_alter_table('api_key', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_api_key_project_id'))

    op.drop_table('api_key')
    op.drop_table('source_ref')
    op.drop_table('project')
    with op.batch_alter_table('entity_audit_log', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_entity_audit_log_target_id'))
        batch_op.drop_index(batch_op.f('ix_entity_audit_log_created_at'))
        batch_op.drop_index(batch_op.f('ix_entity_audit_log_actor'))
        batch_op.drop_index(batch_op.f('ix_entity_audit_log_action'))

    op.drop_table('entity_audit_log')
