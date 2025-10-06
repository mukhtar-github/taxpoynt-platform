"""
Validation Batch Result Model
=============================

Stores summaries of APP validation batches so historical analytics do not
depend solely on FIRS submission records.
"""

import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, JSON, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel


class ValidationBatchResult(BaseModel):
    """Persisted summary for a validation batch execution."""

    __tablename__ = "validation_batch_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)

    batch_id = Column(String(64), nullable=False, index=True)
    validation_id = Column(String(64), nullable=True, index=True)

    total_invoices = Column(Numeric(10, 0), nullable=False, default=0)
    passed_invoices = Column(Numeric(10, 0), nullable=False, default=0)
    failed_invoices = Column(Numeric(10, 0), nullable=False, default=0)

    status = Column(String(32), nullable=False, default="completed")
    error_summary = Column(JSON, nullable=True)
    result_payload = Column(JSON, nullable=True)

    def mark_failed(self) -> None:
        self.status = "failed"
