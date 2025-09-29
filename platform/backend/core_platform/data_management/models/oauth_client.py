"""OAuth 2.0 client registry model for external integrations."""

import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    JSON,
    Text,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


class OAuthClientStatus(str, PyEnum):
    """Lifecycle states for registered OAuth clients."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class OAuthClient(BaseModel):
    """Registered OAuth 2.0 client for external integrations."""

    __tablename__ = "oauth_clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_id = Column(String(64), unique=True, nullable=False, index=True)
    client_secret_hash = Column(String(255), nullable=False)
    client_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # OAuth settings
    allowed_grant_types = Column(JSON, nullable=False, default=list)
    allowed_scopes = Column(JSON, nullable=False, default=list)
    redirect_uris = Column(JSON, nullable=True)
    is_confidential = Column(Boolean, default=True, nullable=False)

    status = Column(Enum(OAuthClientStatus), default=OAuthClientStatus.ACTIVE, nullable=False)

    # Operational metadata
    metadata_blob = Column(JSON, nullable=True)
    last_rotated_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def supports_grant(self, grant_type: str) -> bool:
        grant = (grant_type or "").strip().lower()
        allowed = self.allowed_grant_types or []
        return grant in {g.lower() for g in allowed}

    def allows_scopes(self, scopes: List[str]) -> bool:
        if not scopes:
            return True
        allowed = self.allowed_scopes or []
        allowed_set = {scope.lower() for scope in allowed}
        requested = {scope.lower() for scope in scopes}
        return requested.issubset(allowed_set)

    @property
    def client_metadata(self) -> Dict[str, Any]:
        return dict(self.metadata_blob or {})

    @client_metadata.setter
    def client_metadata(self, value: Optional[Dict[str, Any]]) -> None:
        self.metadata_blob = dict(value or {})
