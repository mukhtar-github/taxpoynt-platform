"""
Async Repository: FIRS Submissions
=================================

Targeted migration module that demonstrates async SQLAlchemy usage and
tenant scoping via ContextVar. Reads the current tenant (organization_id)
from tenant context by default.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.authentication.tenant_context import get_current_tenant
from core_platform.data_management.models.firs_submission import FIRSSubmission


async def list_recent_submissions(
    db: AsyncSession,
    *,
    limit: int = 10,
    organization_id: Optional[UUID | str] = None,
) -> List[FIRSSubmission]:
    """Return recent FIRS submissions for the current tenant (organization).

    If `organization_id` is not provided, uses the tenant context value.
    If neither is available, returns an empty list.
    """
    org_id = organization_id or get_current_tenant()
    if not org_id:
        return []

    stmt = (
        select(FIRSSubmission)
        .where(FIRSSubmission.organization_id == org_id)
        .order_by(desc(FIRSSubmission.created_at))
        .limit(max(1, int(limit)))
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows

