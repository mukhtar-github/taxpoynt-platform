"""
Add indexes for idempotency_keys TTL cleanup

Revision ID: 3a7b2c1d8f21
Revises: 9f2a1c3f6a10
Create Date: 2025-09-20
"""
from alembic import op
import sqlalchemy as sa

revision = '3a7b2c1d8f21'
down_revision = '9f2a1c3f6a10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_idempotency_keys_created_at', 'idempotency_keys', ['created_at'], unique=False)


def downgrade():
    op.drop_index('ix_idempotency_keys_created_at', table_name='idempotency_keys')

