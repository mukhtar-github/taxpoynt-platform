"""seed rbac defaults

Revision ID: b7e1d9c3a4d2
Revises: a3f5c2e7b9a1
Create Date: 2025-09-17 00:15:00.000000
"""

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = 'b7e1d9c3a4d2'
down_revision = 'a3f5c2e7b9a1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    roles_tbl = sa.table(
        'rbac_roles',
        sa.column('id', sa.String),
        sa.column('role_id', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
    )
    perms_tbl = sa.table(
        'rbac_permissions',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('description', sa.String),
    )
    role_perm_tbl = sa.table(
        'rbac_role_permissions',
        sa.column('id', sa.String),
        sa.column('role_id', sa.String),
        sa.column('permission_id', sa.String),
    )
    perm_hier_tbl = sa.table(
        'rbac_permission_hierarchy',
        sa.column('id', sa.String),
        sa.column('parent_permission_id', sa.String),
        sa.column('child_permission_id', sa.String),
    )
    role_inh_tbl = sa.table(
        'rbac_role_inheritance',
        sa.column('id', sa.String),
        sa.column('parent_role_id', sa.String),
        sa.column('child_role_id', sa.String),
    )

    # Define roles with stable IDs for mapping in this migration
    roles = {
        'platform_admin': {
            'id': str(uuid.uuid4()), 'name': 'Platform Admin', 'description': 'Full platform administration'
        },
        'app_admin': {
            'id': str(uuid.uuid4()), 'name': 'APP Admin', 'description': 'Access Point Provider administration'
        },
        'si_admin': {
            'id': str(uuid.uuid4()), 'name': 'SI Admin', 'description': 'System Integrator administration'
        },
        'hybrid_admin': {
            'id': str(uuid.uuid4()), 'name': 'Hybrid Admin', 'description': 'Hybrid SI + APP administration'
        },
        'base_reader': {
            'id': str(uuid.uuid4()), 'name': 'Base Reader', 'description': 'Baseline read-only access'
        },
        'user': {
            'id': str(uuid.uuid4()), 'name': 'User', 'description': 'End user with limited permissions'
        },
    }

    op.bulk_insert(
        roles_tbl,
        [
            {'id': v['id'], 'role_id': k, 'name': v['name'], 'description': v['description']}
            for k, v in roles.items()
        ],
    )

    # Define permissions similarly
    perm_defs = {
        'invoices.read': 'Read invoices',
        'invoices.write': 'Create/update invoices',
        'integrations.read': 'Read integrations',
        'integrations.write': 'Manage integrations',
        'certificates.manage': 'Manage digital certificates',
        'compliance.read': 'View compliance status',
        'taxpayers.manage': 'Manage taxpayer records',
        'organizations.read': 'Read organizations',
        'organizations.write': 'Manage organizations',
    }
    perms = {name: {'id': str(uuid.uuid4()), 'description': desc} for name, desc in perm_defs.items()}

    op.bulk_insert(
        perms_tbl,
        [
            {'id': v['id'], 'name': k, 'description': v['description']}
            for k, v in perms.items()
        ],
    )

    # Permission hierarchy (write implies read)
    hier_pairs = [
        ('invoices.read', 'invoices.write'),
        ('integrations.read', 'integrations.write'),
    ]
    op.bulk_insert(
        perm_hier_tbl,
        [
            {
                'id': str(uuid.uuid4()),
                'parent_permission_id': perms[parent]['id'],
                'child_permission_id': perms[child]['id'],
            }
            for parent, child in hier_pairs
        ],
    )

    # Role → permission assignments
    def rp_rows(role_key: str, perm_names: list[str]):
        return [
            {
                'id': str(uuid.uuid4()),
                'role_id': roles[role_key]['id'],
                'permission_id': perms[p]['id'],
            }
            for p in perm_names
        ]

    rows = []
    rows += rp_rows('platform_admin', list(perm_defs.keys()))
    rows += rp_rows('app_admin', ['invoices.read', 'invoices.write', 'compliance.read', 'taxpayers.manage', 'organizations.read'])
    rows += rp_rows('si_admin', ['integrations.read', 'integrations.write', 'certificates.manage', 'organizations.read'])
    rows += rp_rows('hybrid_admin', ['invoices.read', 'invoices.write', 'compliance.read', 'taxpayers.manage', 'integrations.read', 'integrations.write', 'certificates.manage', 'organizations.read'])
    rows += rp_rows('base_reader', ['integrations.read', 'invoices.read', 'organizations.read'])
    rows += rp_rows('user', ['invoices.read'])

    op.bulk_insert(role_perm_tbl, rows)

    # Role inheritance: hybrid→(app, si), app→base_reader, si→base_reader
    inh_rows = [
        {'id': str(uuid.uuid4()), 'parent_role_id': roles['base_reader']['id'], 'child_role_id': roles['app_admin']['id']},
        {'id': str(uuid.uuid4()), 'parent_role_id': roles['base_reader']['id'], 'child_role_id': roles['si_admin']['id']},
        {'id': str(uuid.uuid4()), 'parent_role_id': roles['app_admin']['id'], 'child_role_id': roles['hybrid_admin']['id']},
        {'id': str(uuid.uuid4()), 'parent_role_id': roles['si_admin']['id'], 'child_role_id': roles['hybrid_admin']['id']},
    ]
    op.bulk_insert(role_inh_tbl, inh_rows)


def downgrade() -> None:
    conn = op.get_bind()
    # Delete role inheritance
    conn.execute(sa.text(
        "DELETE FROM rbac_role_inheritance WHERE parent_role_id IN (SELECT id FROM rbac_roles WHERE role_id IN (:r1,:r2,:r3,:r4,:r5,:r6))"
    ), dict(r1='platform_admin', r2='app_admin', r3='si_admin', r4='hybrid_admin', r5='base_reader', r6='user'))

    # Delete role permissions
    conn.execute(sa.text(
        "DELETE FROM rbac_role_permissions WHERE role_id IN (SELECT id FROM rbac_roles WHERE role_id IN (:r1,:r2,:r3,:r4,:r5,:r6))"
    ), dict(r1='platform_admin', r2='app_admin', r3='si_admin', r4='hybrid_admin', r5='base_reader', r6='user'))

    # Delete permission hierarchy
    conn.execute(sa.text("DELETE FROM rbac_permission_hierarchy WHERE 1=1"))

    # Delete roles
    conn.execute(sa.text(
        "DELETE FROM rbac_roles WHERE role_id IN (:r1,:r2,:r3,:r4,:r5,:r6)"
    ), dict(r1='platform_admin', r2='app_admin', r3='si_admin', r4='hybrid_admin', r5='base_reader', r6='user'))

    # Delete permissions we seeded
    perm_names = ['invoices.read','invoices.write','integrations.read','integrations.write','certificates.manage','compliance.read','taxpayers.manage','organizations.read','organizations.write']
    conn.execute(sa.text(
        "DELETE FROM rbac_permissions WHERE name = ANY(:names)"
    ).bindparams(sa.bindparam('names', expanding=True)), {'names': perm_names})

