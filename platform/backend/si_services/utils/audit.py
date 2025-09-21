"""
Audit Utilities for SI Services
===============================
Thin helpers to write AuditLog entries for SI data/config mutations.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.models import AuditLog, AuditEventType


async def record_audit_event(
    db: AsyncSession,
    *,
    event_type: AuditEventType,
    description: str,
    user_id: Optional[UUID] = None,
    organization_id: Optional[UUID] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    event_data: Optional[Dict[str, Any]] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    compliance_relevant: bool = True,
    retention_days: int = 2555,
    correlation_id: Optional[str] = None,
) -> None:
    entry = AuditLog(
        event_type=event_type,
        event_description=description,
        user_id=user_id,
        organization_id=organization_id,
        target_type=target_type,
        target_id=target_id,
        event_data=event_data or {},
        old_values=old_values or {},
        new_values=new_values or {},
        compliance_relevant=compliance_relevant,
        correlation_id=correlation_id,
        retention_until=datetime.utcnow() + timedelta(days=retention_days),
    )
    db.add(entry)
    await db.commit()
