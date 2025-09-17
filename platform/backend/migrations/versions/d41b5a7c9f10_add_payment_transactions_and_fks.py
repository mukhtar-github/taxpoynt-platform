"""add payment transactions and FKs

Revision ID: d41b5a7c9f10
Revises: c3f7a1d9e2ab
Create Date: 2025-09-17 00:58:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'd41b5a7c9f10'
down_revision = 'c3f7a1d9e2ab'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add FK to organizations on payment_connections.organization_id if not present
    try:
        op.create_foreign_key(
            'fk_payment_connections_org',
            'payment_connections', 'organizations',
            ['organization_id'], ['id'],
            ondelete='SET NULL'
        )
    except Exception:
        pass

    # Create payment_transactions table
    op.create_table(
        'payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('payment_connections.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('provider_transaction_id', sa.String(length=255), nullable=False, index=True),
        sa.Column('amount', sa.String(length=50), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='NGN'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('transaction_metadata', sa.JSON(), nullable=True),
    )
    op.create_index('ix_payment_transactions_id', 'payment_transactions', ['id'])
    op.create_index('ix_payment_transactions_connection_id', 'payment_transactions', ['connection_id'])
    op.create_index('ix_payment_transactions_provider_txn', 'payment_transactions', ['provider_transaction_id'])


def downgrade() -> None:
    op.drop_index('ix_payment_transactions_provider_txn', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_connection_id', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_id', table_name='payment_transactions')
    op.drop_table('payment_transactions')
    try:
        op.drop_constraint('fk_payment_connections_org', 'payment_connections', type_='foreignkey')
    except Exception:
        pass

