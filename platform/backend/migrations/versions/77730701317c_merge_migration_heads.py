"""Merge migration heads

Revision ID: 77730701317c
Revises: 004_add_si_app_correlation, add_user_org_soft_delete, e8f1b7d4c5a9
Create Date: 2025-09-26 12:43:01.706583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77730701317c'
down_revision: Union[str, Sequence[str], None] = ('004_add_si_app_correlation', 'add_user_org_soft_delete', 'e8f1b7d4c5a9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
