"""add payment and reconciliation models

Revision ID: c3f7a1d9e2ab
Revises: b7e1d9c3a4d2
Create Date: 2025-09-17 00:45:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c3f7a1d9e2ab'
down_revision = 'b7e1d9c3a4d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # payment_connections
    op.create_table(
        'payment_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('si_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_connection_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('account_reference', sa.String(length=255), nullable=True),
        sa.Column('connection_metadata', sa.JSON(), nullable=True),
    )
    op.create_index('ix_payment_connections_id', 'payment_connections', ['id'])
    op.create_index('ix_payment_connections_si_id', 'payment_connections', ['si_id'])
    op.create_index('ix_payment_connections_organization_id', 'payment_connections', ['organization_id'])

    # payment_webhooks
    op.create_table(
        'payment_webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_connections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('si_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('endpoint_url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('webhook_metadata', sa.JSON(), nullable=True),
    )
    op.create_index('ix_payment_webhooks_id', 'payment_webhooks', ['id'])
    op.create_index('ix_payment_webhooks_si_id', 'payment_webhooks', ['si_id'])
    op.create_index('ix_payment_webhooks_connection_id', 'payment_webhooks', ['connection_id'])

    # reconciliation_configs
    op.create_table(
        'reconciliation_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('si_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
    )
    op.create_index('ix_reconciliation_configs_id', 'reconciliation_configs', ['id'])
    op.create_index('ix_reconciliation_configs_si_id', 'reconciliation_configs', ['si_id'])
    op.create_index('ix_reconciliation_configs_organization_id', 'reconciliation_configs', ['organization_id'])


def downgrade() -> None:
    op.drop_index('ix_reconciliation_configs_organization_id', table_name='reconciliation_configs')
    op.drop_index('ix_reconciliation_configs_si_id', table_name='reconciliation_configs')
    op.drop_index('ix_reconciliation_configs_id', table_name='reconciliation_configs')
    op.drop_table('reconciliation_configs')

    op.drop_index('ix_payment_webhooks_connection_id', table_name='payment_webhooks')
    op.drop_index('ix_payment_webhooks_si_id', table_name='payment_webhooks')
    op.drop_index('ix_payment_webhooks_id', table_name='payment_webhooks')
    op.drop_table('payment_webhooks')

    op.drop_index('ix_payment_connections_organization_id', table_name='payment_connections')
    op.drop_index('ix_payment_connections_si_id', table_name='payment_connections')
    op.drop_index('ix_payment_connections_id', table_name='payment_connections')
    op.drop_table('payment_connections')
