"""Add SI-APP correlation table

Revision ID: 004_add_si_app_correlation
Revises: 003_add_organization_firs_config
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '004_add_si_app_correlation'
down_revision = 'd41b5a7c9f10'
branch_labels = None
depends_on = None

def upgrade():
    """Add SI-APP correlation table and update organization table."""
    
    # Add firs_configuration to organization table if not exists
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'organizations' AND column_name = 'firs_configuration'
            ) THEN
                ALTER TABLE organizations ADD COLUMN firs_configuration JSON;
            END IF;
        END $$;
    """)
    
    # Create correlation status enum
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'correlationstatus') THEN
                CREATE TYPE correlationstatus AS ENUM (
                    'si_generated',
                    'app_received', 
                    'app_submitting',
                    'app_submitted',
                    'firs_accepted',
                    'firs_rejected',
                    'failed',
                    'cancelled'
                );
            END IF;
        END $$;
    """)
    
    # Create si_app_correlations table
    op.create_table(
        'si_app_correlations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('si_invoice_id', sa.String(length=100), nullable=False),
        sa.Column('si_transaction_ids', postgresql.JSON(), nullable=False),
        sa.Column('irn', sa.String(length=100), nullable=False),
        sa.Column('si_generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('app_submission_id', sa.String(length=100), nullable=True),
        sa.Column('app_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('app_submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('firs_response_id', sa.String(length=100), nullable=True),
        sa.Column('firs_status', sa.String(length=50), nullable=True),
        sa.Column('firs_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_status', sa.Enum('si_generated', 'app_received', 'app_submitting', 'app_submitted', 
                                           'firs_accepted', 'firs_rejected', 'failed', 'cancelled', 
                                           name='correlationstatus'), 
                  nullable=False, server_default='si_generated'),
        sa.Column('last_status_update', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('invoice_number', sa.String(length=100), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='NGN'),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=True),
        sa.Column('customer_tin', sa.String(length=50), nullable=True),
        sa.Column('invoice_data', postgresql.JSON(), nullable=True),
        sa.Column('submission_metadata', postgresql.JSON(), nullable=True),
        sa.Column('firs_response_data', postgresql.JSON(), nullable=True),
        sa.Column('error_details', postgresql.JSON(), nullable=True),
        sa.Column('status_history', postgresql.JSON(), nullable=True),
        sa.Column('retry_count', sa.String(length=10), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.String(length=10), nullable=False, server_default='3'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('correlation_id'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    )
    
    # Create indexes for performance
    op.create_index('idx_si_app_correlations_organization_id', 'si_app_correlations', ['organization_id'])
    op.create_index('idx_si_app_correlations_irn', 'si_app_correlations', ['irn'])
    op.create_index('idx_si_app_correlations_current_status', 'si_app_correlations', ['current_status'])
    op.create_index('idx_si_app_correlations_si_generated_at', 'si_app_correlations', ['si_generated_at'])
    op.create_index('idx_si_app_correlations_last_status_update', 'si_app_correlations', ['last_status_update'])
    op.create_index('idx_si_app_correlations_app_submission_id', 'si_app_correlations', ['app_submission_id'])

def downgrade():
    """Remove SI-APP correlation table."""
    
    # Drop indexes
    op.drop_index('idx_si_app_correlations_app_submission_id', table_name='si_app_correlations')
    op.drop_index('idx_si_app_correlations_last_status_update', table_name='si_app_correlations')
    op.drop_index('idx_si_app_correlations_si_generated_at', table_name='si_app_correlations')
    op.drop_index('idx_si_app_correlations_current_status', table_name='si_app_correlations')
    op.drop_index('idx_si_app_correlations_irn', table_name='si_app_correlations')
    op.drop_index('idx_si_app_correlations_organization_id', table_name='si_app_correlations')
    
    # Drop table
    op.drop_table('si_app_correlations')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS correlationstatus")
    
    # Remove firs_configuration column (optional - might want to keep for other uses)
    # op.drop_column('organizations', 'firs_configuration')
