"""
SI ERP Connection Models
========================

Minimal persistence layer for System Integrator ERP connections. Captures
ownership, configuration metadata, and lifecycle status for the new async
repository pipeline.
"""
from __future__ import annotations

import uuid
import enum
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column,
    String,
    Enum,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import JSON

from .base import BaseModel
import os


def _json_type():
    """Return a JSON-capable column type compatible with the active dialect."""
    db_url = os.getenv("DATABASE_URL", "")
    if "postgresql" in db_url.lower():
        return JSONB
    return JSON


class SIERPConnectionStatus(enum.Enum):
    """Lifecycle status for SI ERP connections."""

    CONFIGURED = "configured"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class SIERPConnection(BaseModel):
    """Persistent representation of an SI ERP connection."""

    __tablename__ = "si_erp_connections"
    __table_args__ = (
        Index("ix_si_erp_connections_org_system", "organization_id", "erp_system"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    erp_system = Column(String(64), nullable=False)
    connection_name = Column(String(255), nullable=False)
    environment = Column(String(50), nullable=False, default="sandbox")

    status = Column(
        Enum(SIERPConnectionStatus, native_enum=False),
        nullable=False,
        default=SIERPConnectionStatus.CONFIGURED,
        server_default=SIERPConnectionStatus.CONFIGURED.value,
    )
    status_reason = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    connection_config = Column(_json_type(), nullable=False, default=dict)
    extra_metadata = Column(_json_type(), nullable=False, default=dict)

    last_status_at = Column(DateTime(timezone=True), nullable=True)

    def mark_status(self, status: SIERPConnectionStatus, *, reason: Optional[str] = None) -> None:
        """Update status-related fields."""
        self.status = status
        self.status_reason = reason
        self.last_status_at = datetime.utcnow()
        if status == SIERPConnectionStatus.DISABLED:
            self.is_active = False
