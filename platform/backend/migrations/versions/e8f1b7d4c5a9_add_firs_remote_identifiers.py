"""Add columns for FIRS-issued IRN metadata (CSID/QR).

Revision ID: e8f1b7d4c5a9
Revises: 3a7b2c1d8f21
Create Date: 2025-09-28
"""
from alembic import op
import sqlalchemy as sa


revision = 'e8f1b7d4c5a9'
down_revision = '3a7b2c1d8f21'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('firs_submissions', sa.Column('csid', sa.String(length=255), nullable=True))
    op.add_column('firs_submissions', sa.Column('csid_hash', sa.String(length=512), nullable=True))
    op.add_column('firs_submissions', sa.Column('qr_payload', sa.JSON(), nullable=True))
    op.add_column('firs_submissions', sa.Column('firs_stamp_metadata', sa.JSON(), nullable=True))
    op.add_column('firs_submissions', sa.Column('firs_received_at', sa.DateTime(timezone=True), nullable=True))

    op.create_index('ix_firs_submissions_csid', 'firs_submissions', ['csid'], unique=False)
    op.create_index('ix_firs_submissions_firs_received_at', 'firs_submissions', ['firs_received_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_firs_submissions_firs_received_at', table_name='firs_submissions')
    op.drop_index('ix_firs_submissions_csid', table_name='firs_submissions')

    op.drop_column('firs_submissions', 'firs_received_at')
    op.drop_column('firs_submissions', 'firs_stamp_metadata')
    op.drop_column('firs_submissions', 'qr_payload')
    op.drop_column('firs_submissions', 'csid_hash')
    op.drop_column('firs_submissions', 'csid')
