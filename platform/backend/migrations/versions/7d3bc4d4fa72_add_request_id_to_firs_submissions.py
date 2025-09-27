"""Add request_id to firs_submissions

Revision ID: 7d3bc4d4fa72
Revises: 8891f9a2b7c4
Create Date: 2025-02-17 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7d3bc4d4fa72"
down_revision = "8891f9a2b7c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "firs_submissions",
        sa.Column("request_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_firs_submissions_request_id",
        "firs_submissions",
        ["request_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_firs_submissions_request_id", table_name="firs_submissions")
    op.drop_column("firs_submissions", "request_id")
