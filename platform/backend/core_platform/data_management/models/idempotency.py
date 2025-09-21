"""
Idempotency Models
==================
Async SQLAlchemy model for storing idempotency keys and responses.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum as SAEnum,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel
from .business_systems import get_json_type
from enum import Enum as PyEnum


class IdempotencyStatus(str, PyEnum):  # type: ignore[misc]
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class IdempotencyKey(BaseModel):
    """Persisted idempotency records for safe retries of write operations."""

    __tablename__ = "idempotency_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Uniqueness scoped by requester for safety
    requester_id = Column(UUID(as_uuid=True), nullable=True)
    key = Column(String(255), nullable=False)

    # Request identity
    method = Column(String(10), nullable=False)
    endpoint = Column(String(500), nullable=False)
    request_hash = Column(String(64), nullable=False)

    # Lifecycle
    status = Column(SAEnum(IdempotencyStatus), nullable=False, default=IdempotencyStatus.IN_PROGRESS)
    status_code = Column(Integer, nullable=True)
    response_data = Column(get_json_type(), default={})

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        # Ensure replay with same key+requester is deduped
        UniqueConstraint("requester_id", "key", name="uq_idem_requester_key"),
    )
