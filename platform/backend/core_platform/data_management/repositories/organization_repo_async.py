"""
Async repository for Organizations (minimal reads).

Provides a lightweight listing helper with optional filters suitable for
SI read endpoints. This avoids pulling in broader relationships and keeps
queries efficient and simple for pagination.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, Union, List
import time
import uuid
from uuid import UUID as UUIDType

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core_platform.data_management.models.organization import Organization, OrganizationStatus
from core_platform.monitoring.prometheus_integration import get_prometheus_integration


async def list_organizations(
    db: AsyncSession,
    *,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List organizations with optional filters and pagination.

    - search: matches name/tin/rc_number (ILIKE where supported; basic LIKE otherwise)
    - status: OrganizationStatus enum name (case-insensitive)
    Returns a dict with items, count, page, limit, and offset.
    """
    page = max(1, int(page))
    limit = max(1, int(limit))
    offset = (page - 1) * limit

    stmt = select(Organization)

    # Status filter
    if status:
        try:
            st = OrganizationStatus[status.upper()]
            stmt = stmt.where(Organization.status == st)
        except KeyError:
            return {"items": [], "count": 0, "page": page, "limit": limit, "offset": offset}

    # Search filter (simple LIKE on common fields)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            (Organization.name.like(pattern))
            | (Organization.tin.like(pattern))
            | (Organization.rc_number.like(pattern))
        )

    # Total count
    count_stmt = stmt.with_only_columns(func.count(Organization.id))

    def to_dict(org: Organization) -> Dict[str, Any]:
        return {
            "id": str(getattr(org, "id", None)),
            "name": getattr(org, "name", None),
            "business_type": getattr(org, "business_type", None).value if getattr(org, "business_type", None) else None,
            "tin": getattr(org, "tin", None),
            "rc_number": getattr(org, "rc_number", None),
            "status": getattr(org, "status", None).value if getattr(org, "status", None) else None,
            "created_at": getattr(org, "created_at", None).isoformat() if getattr(org, "created_at", None) else None,
        }

    start = time.monotonic()
    outcome = "success"
    try:
        total = (await db.execute(count_stmt)).scalar_one_or_none() or 0

        # Page
        page_stmt = stmt.order_by(Organization.created_at.desc()).offset(offset).limit(limit)
        rows = (await db.execute(page_stmt)).scalars().all()

        return {
                "items": [to_dict(r) for r in rows],
                "count": int(total),
                "page": page,
                "limit": limit,
                "offset": offset,
            }
    except Exception:
        outcome = "error"
        raise
    finally:
        dt = time.monotonic() - start
        integ = get_prometheus_integration()
        if integ:
            integ.record_metric(
                "taxpoynt_repository_queries_total", 1,
                {"repository": "organization", "method": "list_organizations", "table": "organizations", "outcome": outcome}
            )
            integ.record_metric(
                "taxpoynt_repository_query_duration_seconds", dt,
                {"repository": "organization", "method": "list_organizations", "table": "organizations"}
            )


async def get_organization_by_id(
    db: AsyncSession, *, organization_id: Union[UUIDType, str]
) -> Optional[Dict[str, Any]]:
    """Get minimal organization details by ID."""
    if isinstance(organization_id, uuid.UUID):
        org_id = organization_id
    else:
        try:
            org_id = uuid.UUID(str(organization_id))
        except Exception:
            return None

    start = time.monotonic()
    outcome = "success"
    try:
        row = (await db.execute(select(Organization).where(Organization.id == org_id))).scalars().first()
        if not row:
            return None

        return {
            "id": str(getattr(row, "id", None)),
            "name": getattr(row, "name", None),
            "business_type": getattr(row, "business_type", None).value if getattr(row, "business_type", None) else None,
            "tin": getattr(row, "tin", None),
            "rc_number": getattr(row, "rc_number", None),
            "status": getattr(row, "status", None).value if getattr(row, "status", None) else None,
            "created_at": getattr(row, "created_at", None).isoformat() if getattr(row, "created_at", None) else None,
        }
    except Exception:
        outcome = "error"
        raise
    finally:
        dt = time.monotonic() - start
        integ = get_prometheus_integration()
        if integ:
            integ.record_metric(
                "taxpoynt_repository_queries_total", 1,
                {"repository": "organization", "method": "get_organization_by_id", "table": "organizations", "outcome": outcome}
            )
            integ.record_metric(
                "taxpoynt_repository_query_duration_seconds", dt,
                {"repository": "organization", "method": "get_organization_by_id", "table": "organizations"}
            )


async def list_organizations_by_system(
    db: AsyncSession,
    *,
    system_type: str,
    page: int = 1,
    limit: int = 50,
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """List organizations that have at least one connection of a given system type.

    Supports: erp, crm, pos, banking. Others return empty for now.
    """
    from core_platform.data_management.models.business_systems import (
        ERPConnection, CRMConnection, POSConnection,
    )
    from core_platform.data_management.models.banking import BankingConnection

    model_map = {
        "erp": ERPConnection,
        "crm": CRMConnection,
        "pos": POSConnection,
        "banking": BankingConnection,
    }
    sys_key = (system_type or "").lower()
    conn_model = model_map.get(sys_key)
    if not conn_model:
        return {"items": [], "count": 0, "page": page, "limit": limit, "offset": 0}

    page = max(1, int(page))
    limit = max(1, int(limit))
    offset = (page - 1) * limit

    base = select(Organization).join(conn_model, conn_model.organization_id == Organization.id)

    if status:
        try:
            st = OrganizationStatus[status.upper()]
            base = base.where(Organization.status == st)
        except KeyError:
            return {"items": [], "count": 0, "page": page, "limit": limit, "offset": offset}

    if search:
        pattern = f"%{search}%"
        base = base.where(
            (Organization.name.like(pattern))
            | (Organization.tin.like(pattern))
            | (Organization.rc_number.like(pattern))
        )

    def to_dict(org: Organization) -> Dict[str, Any]:
        return {
            "id": str(getattr(org, "id", None)),
            "name": getattr(org, "name", None),
            "business_type": getattr(org, "business_type", None).value if getattr(org, "business_type", None) else None,
            "tin": getattr(org, "tin", None),
            "rc_number": getattr(org, "rc_number", None),
            "status": getattr(org, "status", None).value if getattr(org, "status", None) else None,
            "created_at": getattr(org, "created_at", None).isoformat() if getattr(org, "created_at", None) else None,
        }

    start = time.monotonic()
    outcome = "success"
    try:
        count_stmt = select(func.count(func.distinct(Organization.id))).select_from(base.subquery())
        total = (await db.execute(count_stmt)).scalar_one_or_none() or 0

        page_stmt = (
            base.order_by(Organization.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = (await db.execute(page_stmt)).scalars().all()

        return {
                "items": [to_dict(r) for r in rows],
                "count": int(total),
                "page": page,
                "limit": limit,
                "offset": offset,
                "system_type": sys_key,
            }
    except Exception:
        outcome = "error"
        raise
    finally:
        dt = time.monotonic() - start
        integ = get_prometheus_integration()
        if integ:
            integ.record_metric(
                "taxpoynt_repository_queries_total", 1,
                {"repository": "organization", "method": "list_organizations_by_system", "table": "organizations", "outcome": outcome}
            )
            integ.record_metric(
                "taxpoynt_repository_query_duration_seconds", dt,
                {"repository": "organization", "method": "list_organizations_by_system", "table": "organizations"}
            )
