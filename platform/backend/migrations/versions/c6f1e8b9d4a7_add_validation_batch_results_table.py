"""Add validation batch results table

Revision ID: c6f1e8b9d4a7
Revises: da3231961a92
Create Date: 2025-10-05 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c6f1e8b9d4a7"
down_revision: Union[str, Sequence[str], None] = "da3231961a92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "validation_batch_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=False),
        sa.Column("validation_id", sa.String(length=64), nullable=True),
        sa.Column(
            "total_invoices",
            sa.Numeric(precision=10, scale=0),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "passed_invoices",
            sa.Numeric(precision=10, scale=0),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "failed_invoices",
            sa.Numeric(precision=10, scale=0),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'completed'"),
        ),
        sa.Column("error_summary", sa.JSON(), nullable=True),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint([
            "organization_id"
        ], ["organizations.id"], name=op.f("fk_validation_batch_results_organization_id_organizations")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_validation_batch_results")),
    )

    op.create_index(
        op.f("ix_validation_batch_results_batch_id"),
        "validation_batch_results",
        ["batch_id"],
    )
    op.create_index(
        op.f("ix_validation_batch_results_validation_id"),
        "validation_batch_results",
        ["validation_id"],
    )
    op.create_index(
        op.f("ix_validation_batch_results_organization_id"),
        "validation_batch_results",
        ["organization_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_validation_batch_results_organization_id"),
        table_name="validation_batch_results",
    )
    op.drop_index(
        op.f("ix_validation_batch_results_validation_id"),
        table_name="validation_batch_results",
    )
    op.drop_index(
        op.f("ix_validation_batch_results_batch_id"),
        table_name="validation_batch_results",
    )
    op.drop_table("validation_batch_results")
