"""Add FIRS submission stamp columns

Revision ID: 8891f9a2b7c4
Revises: 77730701317c
Create Date: 2025-09-26 14:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8891f9a2b7c4'
down_revision = '77730701317c'
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return column in [col["name"] for col in inspector.get_columns(table)]


def upgrade() -> None:
    if not _has_column('firs_submissions', 'csid'):
        op.add_column('firs_submissions', sa.Column('csid', sa.String(length=255), nullable=True))
    if not _has_column('firs_submissions', 'csid_hash'):
        op.add_column('firs_submissions', sa.Column('csid_hash', sa.String(length=512), nullable=True))
    if not _has_column('firs_submissions', 'qr_payload'):
        op.add_column('firs_submissions', sa.Column('qr_payload', sa.JSON(), nullable=True))
    if not _has_column('firs_submissions', 'firs_stamp_metadata'):
        op.add_column('firs_submissions', sa.Column('firs_stamp_metadata', sa.JSON(), nullable=True))

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('firs_submissions')}
    if 'ix_firs_submissions_csid' not in existing_indexes:
        op.create_index('ix_firs_submissions_csid', 'firs_submissions', ['csid'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('firs_submissions')}
    if 'ix_firs_submissions_csid' in existing_indexes:
        op.drop_index('ix_firs_submissions_csid', table_name='firs_submissions')

    for column in ['firs_stamp_metadata', 'qr_payload', 'csid_hash', 'csid']:
        if _has_column('firs_submissions', column):
            op.drop_column('firs_submissions', column)
