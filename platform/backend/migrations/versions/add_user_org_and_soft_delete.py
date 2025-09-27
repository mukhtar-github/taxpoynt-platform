"""Add organization_id and soft delete fields to users and organizations

Revision ID: add_user_org_soft_delete
Revises: add_sdk_management_models
Create Date: 2025-08-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'add_user_org_soft_delete'
down_revision: Union[str, Sequence[str], None] = 'add_sdk_management_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add organization_id and soft delete fields."""
    
    # Add organization_id to users table
    op.add_column('users', sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint for organization_id
    op.create_foreign_key(
        'fk_users_organization_id',
        'users', 
        'organizations',
        ['organization_id'], 
        ['id'],
        ondelete='CASCADE'
    )
    
    # Add soft delete fields to users table
    op.add_column('users', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    
    # Add soft delete fields to organizations table
    op.add_column('organizations', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.add_column('organizations', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove organization_id and soft delete fields."""
    
    # Remove soft delete fields from organizations table
    op.drop_column('organizations', 'deleted_at')
    op.drop_column('organizations', 'is_deleted')
    
    # Remove soft delete fields from users table  
    op.drop_column('users', 'deleted_at')
    op.drop_column('users', 'is_deleted')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    
    # Remove organization_id from users table
    op.drop_column('users', 'organization_id')
