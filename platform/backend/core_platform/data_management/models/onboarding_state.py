"""Onboarding state persistence model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, String, Boolean, Index
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class OnboardingStateORM(Base):
    __tablename__ = "onboarding_states"

    user_id = Column(String, primary_key=True, index=True)
    service_package = Column(String, nullable=False, index=True)
    current_step = Column(String, nullable=False, index=True)
    completed_steps = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=list)
    has_started = Column(Boolean, nullable=False, default=True)
    is_complete = Column(Boolean, nullable=False, default=False)
    state_metadata = Column("metadata", JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    last_active_date = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("ix_onboarding_state_service_package", "service_package"),
    )


def serialize_completed_steps(steps: List[str]) -> List[str]:
    # Ensure JSON serializable list of unique steps while preserving order
    seen = set()
    ordered: List[str] = []
    for step in steps:
        if step not in seen:
            seen.add(step)
            ordered.append(step)
    return ordered


def merge_metadata(base: Dict[str, Any], updates: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not updates:
        return base
    result = {**base}
    result.update(updates)
    return result
