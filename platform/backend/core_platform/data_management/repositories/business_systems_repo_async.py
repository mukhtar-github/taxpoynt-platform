"""
Async repository for business systems (minimal): ERP connections only.

Provides list operations with tenant scoping and pagination. Supports
`system_type="erp"` for now; other types return empty lists to avoid broad
schema dependencies in this targeted migration.
"""
from __future__ import annotations

from typing import List, Optional, Union, Dict, Any
import uuid
from uuid import UUID as UUIDType

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core_platform.authentication.tenant_context import get_current_tenant
from core_platform.data_management.models.business_systems import ERPConnection


async def list_business_systems(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    system_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    """List business systems for a tenant with pagination.

    Currently supports only `system_type="erp"`. Others return empty list.
    Returns dict with `items` and `count`.
    """
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {"items": [], "count": 0}
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return {"items": [], "count": 0}

    if system_type and system_type.lower() != "erp":
        return {"items": [], "count": 0}

    # ERP connections
    base = select(ERPConnection).where(ERPConnection.organization_id == org_id)
    total = (await db.execute(base)).scalars().all()
    stmt = base.order_by(ERPConnection.created_at.desc()).offset(max(0, int(offset))).limit(max(1, int(limit)))
    res = await db.execute(stmt)
    rows = res.scalars().all()

    def to_dict(row: ERPConnection) -> Dict[str, Any]:
        return {
            "id": str(getattr(row, "id", None)),
            "provider": getattr(row, "provider", None).value if getattr(row, "provider", None) else None,
            "system_name": getattr(row, "system_name", None),
            "status": getattr(row, "status", None).value if getattr(row, "status", None) else None,
            "is_active": bool(getattr(row, "is_active", False)),
            "last_sync_at": getattr(row, "last_sync_at", None).isoformat() if getattr(row, "last_sync_at", None) else None,
            "next_sync_at": getattr(row, "next_sync_at", None).isoformat() if getattr(row, "next_sync_at", None) else None,
            "version": getattr(row, "version", None),
        }

    return {"items": [to_dict(r) for r in rows], "count": len(total)}

