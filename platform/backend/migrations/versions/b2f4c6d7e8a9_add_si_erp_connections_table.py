"""Add SI ERP connections table

Revision ID: b2f4c6d7e8a9
Revises: f9c2d1a3b5e6
Create Date: 2025-10-08 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b2f4c6d7e8a9"
down_revision: Union[str, Sequence[str], None] = "f9c2d1a3b5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


si_erp_status_enum = sa.Enum(
    "configured",
    "active",
    "error",
    "disabled",
    name="ck_si_erp_connections_status",
    native_enum=False,
)


def _json_column() -> sa.types.TypeEngine:
    """Return a JSON column compatible with Postgres and SQLite."""
    return sa.JSON().with_variant(
        postgresql.JSONB(astext_type=sa.Text()),
        "postgresql",
    )


def upgrade() -> None:
    op.execute("DROP TYPE IF EXISTS sierpconnectionstatus")

    op.create_table(
        "si_erp_connections",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("organization_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "owner_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("erp_system", sa.String(length=64), nullable=False),
        sa.Column("connection_name", sa.String(length=255), nullable=False),
        sa.Column(
            "environment",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'sandbox'"),
        ),
        sa.Column(
            "status",
            si_erp_status_enum,
            nullable=False,
            server_default=sa.text("'configured'"),
        ),
        sa.Column("status_reason", sa.String(length=255), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("connection_config", _json_column(), nullable=False),
        sa.Column("extra_metadata", _json_column(), nullable=False),
        sa.Column("last_status_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index(
        "ix_si_erp_connections_org",
        "si_erp_connections",
        ["organization_id"],
    )
    op.create_index(
        "ix_si_erp_connections_owner",
        "si_erp_connections",
        ["owner_user_id"],
    )
    op.create_index(
        "ix_si_erp_connections_org_system",
        "si_erp_connections",
        ["organization_id", "erp_system"],
    )


def downgrade() -> None:
    op.drop_index("ix_si_erp_connections_org_system", table_name="si_erp_connections")
    op.drop_index("ix_si_erp_connections_owner", table_name="si_erp_connections")
    op.drop_index("ix_si_erp_connections_org", table_name="si_erp_connections")
    op.drop_table("si_erp_connections")
    bind = op.get_bind()
    si_erp_status_enum.drop(bind, checkfirst=True)
