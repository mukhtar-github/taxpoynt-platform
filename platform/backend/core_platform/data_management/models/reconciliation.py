"""
Reconciliation Models
=====================

Persist reconciliation configurations for SI.
"""
from __future__ import annotations

import uuid
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel
from .banking import get_json_type


class ReconciliationConfig(BaseModel):
    __tablename__ = "reconciliation_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    si_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    config = Column(get_json_type(), default={})

