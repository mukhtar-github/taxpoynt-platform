"""add rbac models and inheritance

Revision ID: a3f5c2e7b9a1
Revises: 920b8e791d92
Create Date: 2025-09-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'a3f5c2e7b9a1'
down_revision = '920b8e791d92'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # rbac_roles
    op.create_table(
        'rbac_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('role_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.UniqueConstraint('role_id', name='uq_rbac_role_role_id'),
    )
    op.create_index('ix_rbac_roles_id', 'rbac_roles', ['id'])
    op.create_index('ix_rbac_roles_role_id', 'rbac_roles', ['role_id'])

    # rbac_permissions
    op.create_table(
        'rbac_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.UniqueConstraint('name', name='uq_rbac_permission_name'),
    )
    op.create_index('ix_rbac_permissions_id', 'rbac_permissions', ['id'])
    op.create_index('ix_rbac_permissions_name', 'rbac_permissions', ['name'])

    # rbac_role_permissions
    op.create_table(
        'rbac_role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rbac_roles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rbac_permissions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )
    op.create_index('ix_rbac_role_permissions_id', 'rbac_role_permissions', ['id'])
    op.create_index('ix_rbac_role_permissions_role_id', 'rbac_role_permissions', ['role_id'])
    op.create_index('ix_rbac_role_permissions_permission_id', 'rbac_role_permissions', ['permission_id'])

    # rbac_permission_hierarchy
    op.create_table(
        'rbac_permission_hierarchy',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parent_permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rbac_permissions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('child_permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rbac_permissions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.UniqueConstraint('parent_permission_id', 'child_permission_id', name='uq_permission_hierarchy'),
    )
    op.create_index('ix_rbac_permission_hierarchy_id', 'rbac_permission_hierarchy', ['id'])
    op.create_index('ix_rbac_permission_hierarchy_parent', 'rbac_permission_hierarchy', ['parent_permission_id'])
    op.create_index('ix_rbac_permission_hierarchy_child', 'rbac_permission_hierarchy', ['child_permission_id'])

    # rbac_role_inheritance
    op.create_table(
        'rbac_role_inheritance',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('parent_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rbac_roles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('child_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rbac_roles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.UniqueConstraint('parent_role_id', 'child_role_id', name='uq_role_inheritance'),
    )
    op.create_index('ix_rbac_role_inheritance_id', 'rbac_role_inheritance', ['id'])
    op.create_index('ix_rbac_role_inheritance_parent', 'rbac_role_inheritance', ['parent_role_id'])
    op.create_index('ix_rbac_role_inheritance_child', 'rbac_role_inheritance', ['child_role_id'])


def downgrade() -> None:
    op.drop_index('ix_rbac_role_inheritance_child', table_name='rbac_role_inheritance')
    op.drop_index('ix_rbac_role_inheritance_parent', table_name='rbac_role_inheritance')
    op.drop_index('ix_rbac_role_inheritance_id', table_name='rbac_role_inheritance')
    op.drop_table('rbac_role_inheritance')

    op.drop_index('ix_rbac_permission_hierarchy_child', table_name='rbac_permission_hierarchy')
    op.drop_index('ix_rbac_permission_hierarchy_parent', table_name='rbac_permission_hierarchy')
    op.drop_index('ix_rbac_permission_hierarchy_id', table_name='rbac_permission_hierarchy')
    op.drop_table('rbac_permission_hierarchy')

    op.drop_index('ix_rbac_role_permissions_permission_id', table_name='rbac_role_permissions')
    op.drop_index('ix_rbac_role_permissions_role_id', table_name='rbac_role_permissions')
    op.drop_index('ix_rbac_role_permissions_id', table_name='rbac_role_permissions')
    op.drop_table('rbac_role_permissions')

    op.drop_index('ix_rbac_permissions_name', table_name='rbac_permissions')
    op.drop_index('ix_rbac_permissions_id', table_name='rbac_permissions')
    op.drop_table('rbac_permissions')

    op.drop_index('ix_rbac_roles_role_id', table_name='rbac_roles')
    op.drop_index('ix_rbac_roles_id', table_name='rbac_roles')
    op.drop_table('rbac_roles')

