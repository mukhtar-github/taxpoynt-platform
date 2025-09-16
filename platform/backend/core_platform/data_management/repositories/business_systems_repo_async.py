"""
Async repository for business systems (minimal): ERP connections only.

Provides list operations with tenant scoping and pagination. Supports
`system_type="erp"` for now; other types return empty lists to avoid broad
schema dependencies in this targeted migration.
"""
from __future__ import annotations

from typing import List, Optional, Union, Dict, Any
import time
import uuid
from uuid import UUID as UUIDType

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core_platform.authentication.tenant_context import get_current_tenant
from core_platform.data_management.models.business_systems import (
    ERPConnection, CRMConnection, POSConnection,
    ERPProvider, CRMProvider, POSProvider, SyncStatus,
)
from core_platform.data_management.models.banking import (
    BankingConnection, BankingProvider, ConnectionStatus,
)
from core_platform.monitoring.prometheus_integration import get_prometheus_integration


async def list_business_systems(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    system_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    provider: Optional[str] = None,
    status: Optional[str] = None,
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

    sys_type = (system_type or "erp").lower()

    # Choose model and field mapping
    if sys_type == "erp":
        model = ERPConnection
        prov_enum = ERPProvider
        prov_attr = ERPConnection.provider
        status_attr = ERPConnection.status
        status_enum = SyncStatus
        name_field = "system_name"
        last_field = "last_sync_at"
    elif sys_type == "crm":
        model = CRMConnection
        prov_enum = CRMProvider
        prov_attr = CRMConnection.provider
        status_attr = CRMConnection.status
        status_enum = SyncStatus
        name_field = "system_name"
        last_field = "last_sync_at"
    elif sys_type == "pos":
        model = POSConnection
        prov_enum = POSProvider
        prov_attr = POSConnection.provider
        status_attr = POSConnection.status
        status_enum = SyncStatus
        name_field = "device_name"
        last_field = "last_transaction_sync"
    elif sys_type == "banking":
        model = BankingConnection
        prov_enum = BankingProvider
        prov_attr = BankingConnection.provider
        status_attr = BankingConnection.status
        status_enum = ConnectionStatus
        name_field = "bank_name"
        last_field = "last_sync_at"
    else:
        return {"items": [], "count": 0}

    base = select(model).where(model.organization_id == org_id)

    # Provider filter
    if provider:
        try:
            p = prov_enum[provider.upper()]
            base = base.where(prov_attr == p)
        except KeyError:
            return {"items": [], "count": 0}

    # Status filter
    if status:
        try:
            st = status_enum[status.upper()]
            base = base.where(status_attr == st)
        except KeyError:
            return {"items": [], "count": 0}

    def _mask_account_number(acc: Optional[str]) -> Optional[str]:
        if not acc or not isinstance(acc, str):
            return None
        tail = acc[-4:]
        return f"****{tail}"

    def to_dict(row) -> Dict[str, Any]:
        base = {
            "id": str(getattr(row, "id", None)),
            "provider": getattr(row, "provider", None).value if getattr(row, "provider", None) else None,
            name_field: getattr(row, name_field, None),
            "status": getattr(row, "status", None).value if getattr(row, "status", None) else None,
            "is_active": bool(getattr(row, "is_active", False)) if hasattr(row, "is_active") else None,
            last_field: getattr(row, last_field, None).isoformat() if getattr(row, last_field, None) else None,
        }
        # ERP may have version
        if hasattr(row, "version"):
            base["version"] = getattr(row, "version", None)
        # Banking extras with masking
        if sys_type == "banking":
            base.update({
                "bank_name": getattr(row, "bank_name", None),
                "bank_code": getattr(row, "bank_code", None),
                "account_name": getattr(row, "account_name", None),
                "masked_account_number": _mask_account_number(getattr(row, "account_number", None)),
                "provider_account_id": getattr(row, "provider_account_id", None),
            })
        return base

    start = time.monotonic()
    outcome = "success"
    try:
        # Count (naive)
        total_rows = (await db.execute(base)).scalars().all()
        stmt = base.order_by(getattr(model, "created_at").desc()).offset(max(0, int(offset))).limit(max(1, int(limit)))
        rows = (await db.execute(stmt)).scalars().all()

        return {
                "items": [to_dict(r) for r in rows],
                "count": len(total_rows),
                "limit": int(limit),
                "offset": int(offset),
                "system_type": sys_type,
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
                {"repository": "business_systems", "method": "list_business_systems", "table": "business_systems", "outcome": outcome}
            )
            integ.record_metric(
                "taxpoynt_repository_query_duration_seconds", dt,
                {"repository": "business_systems", "method": "list_business_systems", "table": "business_systems"}
            )
