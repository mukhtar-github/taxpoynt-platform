"""Initial migration: Create all tables

Revision ID: 3222e08973f1
Revises: 
Create Date: 2025-08-13 16:43:24.891509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3222e08973f1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('email_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('role', sa.Enum('system_integrator', 'access_point_provider', 'hybrid_user', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('registration_number', sa.String(length=100), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tax_id')
    )

    # Create user_service_access table  
    op.create_table('user_service_access',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('service_type', sa.Enum('firs_integration', 'invoice_generation', 'compliance_monitoring', name='servicetype'), nullable=False),
        sa.Column('access_level', sa.Enum('read', 'write', 'admin', name='accesslevel'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create organization_users table
    op.create_table('organization_users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', 'viewer', name='organizationrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'user_id')
    )

    # Create integrations table
    op.create_table('integrations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('integration_type', sa.Enum('erp', 'crm', 'pos', 'accounting', 'other', name='integrationtype'), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('status', sa.Enum('active', 'inactive', 'error', 'pending', name='integrationstatus'), nullable=False, default='pending'),
        sa.Column('config_data', sa.JSON(), nullable=True),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create integration_credentials table
    op.create_table('integration_credentials',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('integration_id', sa.String(length=36), nullable=False),
        sa.Column('credential_type', sa.Enum('api_key', 'oauth_token', 'username_password', 'certificate', name='credentialtype'), nullable=False),
        sa.Column('encrypted_data', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create firs_submissions table
    op.create_table('firs_submissions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('invoice_id', sa.String(length=100), nullable=False),
        sa.Column('submission_type', sa.Enum('invoice', 'credit_note', 'debit_note', name='submissiontype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'submitted', 'accepted', 'rejected', 'cancelled', name='submissionstatus'), nullable=False, default='pending'),
        sa.Column('firs_reference', sa.String(length=100), nullable=True),
        sa.Column('submission_data', sa.JSON(), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('invoice_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (to handle foreign key constraints)
    op.drop_table('firs_submissions')
    op.drop_table('integration_credentials')
    op.drop_table('integrations')
    op.drop_table('organization_users')
    op.drop_table('user_service_access')
    op.drop_table('organizations')
    op.drop_table('users')
    
    # Drop custom enums
    op.execute('DROP TYPE IF EXISTS submissionstatus')
    op.execute('DROP TYPE IF EXISTS submissiontype')
    op.execute('DROP TYPE IF EXISTS credentialtype')
    op.execute('DROP TYPE IF EXISTS integrationstatus')
    op.execute('DROP TYPE IF EXISTS integrationtype')
    op.execute('DROP TYPE IF EXISTS organizationrole')
    op.execute('DROP TYPE IF EXISTS accesslevel')
    op.execute('DROP TYPE IF EXISTS servicetype')
    op.execute('DROP TYPE IF EXISTS userrole')
