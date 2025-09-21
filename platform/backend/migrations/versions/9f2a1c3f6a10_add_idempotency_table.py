"""
Add idempotency_keys table for SI/App idempotent operations

Revision ID: 9f2a1c3f6a10
Revises: 920b8e791d92
Create Date: 2025-09-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '9f2a1c3f6a10'
down_revision = '920b8e791d92'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'idempotency_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('request_hash', sa.String(length=64), nullable=False),
        sa.Column('status', sa.Enum('in_progress', 'succeeded', 'failed', name='idempotencystatus'), nullable=False, server_default='in_progress'),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_idempotency_keys')),
        sa.UniqueConstraint('requester_id', 'key', name=op.f('uq_idem_requester_key')),
    )


def downgrade():
    op.drop_table('idempotency_keys')
    op.execute("DROP TYPE IF EXISTS idempotencystatus")

