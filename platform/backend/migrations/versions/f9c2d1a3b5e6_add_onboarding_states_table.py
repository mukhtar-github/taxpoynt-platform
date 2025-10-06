"""Add onboarding states table

Revision ID: f9c2d1a3b5e6
Revises: c6f1e8b9d4a7
Create Date: 2025-10-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f9c2d1a3b5e6"
down_revision: Union[str, Sequence[str], None] = "c6f1e8b9d4a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "onboarding_states",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("service_package", sa.String(length=16), nullable=False),
        sa.Column("current_step", sa.String(length=128), nullable=False),
        sa.Column(
            "completed_steps",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("has_started", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_complete", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_active_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_onboarding_states")),
    )

    op.create_index(op.f("ix_onboarding_states_service_package"), "onboarding_states", ["service_package"])
    op.create_index(op.f("ix_onboarding_states_current_step"), "onboarding_states", ["current_step"])
    op.create_index(op.f("ix_onboarding_states_last_active_date"), "onboarding_states", ["last_active_date"])


def downgrade() -> None:
    op.drop_index(op.f("ix_onboarding_states_last_active_date"), table_name="onboarding_states")
    op.drop_index(op.f("ix_onboarding_states_current_step"), table_name="onboarding_states")
    op.drop_index(op.f("ix_onboarding_states_service_package"), table_name="onboarding_states")
    op.drop_table("onboarding_states")
