"""Add oauth_clients table

Revision ID: da3231961a92
Revises: 7d3bc4d4fa72
Create Date: 2025-09-29 08:44:28.546622

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "da3231961a92"
down_revision: Union[str, Sequence[str], None] = "7d3bc4d4fa72"
branch_labels = None
depends_on = None


ENUM_EXISTS_SQL = """
SELECT 1 FROM pg_type WHERE typname = 'oauthclientstatus'
"""

ENUM_CREATE_SQL = """
CREATE TYPE oauthclientstatus AS ENUM ('active', 'suspended', 'revoked')
"""

ENUM_DROP_SQL = """
DROP TYPE IF EXISTS oauthclientstatus
"""


def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.execute(sa.text(ENUM_EXISTS_SQL)).fetchone()
    if not exists:
        bind.execute(sa.text(ENUM_CREATE_SQL))

    op.create_table(
        "oauth_clients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.String(length=64), nullable=False),
        sa.Column("client_secret_hash", sa.String(length=255), nullable=False),
        sa.Column("client_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("allowed_grant_types", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("allowed_scopes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("redirect_uris", sa.JSON(), nullable=True),
        sa.Column("is_confidential", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "status",
            postgresql.ENUM("active", "suspended", "revoked", name="oauthclientstatus", create_type=False),
            nullable=False,
            server_default=sa.text("'active'::oauthclientstatus"),
        ),
        sa.Column("metadata_blob", sa.JSON(), nullable=True, server_default=sa.text("'{}'::json")),
        sa.Column("last_rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_oauth_clients_client_id"),
        "oauth_clients",
        ["client_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_oauth_clients_client_id"), table_name="oauth_clients")
    op.drop_table("oauth_clients")
    op.execute(sa.text(ENUM_DROP_SQL))
