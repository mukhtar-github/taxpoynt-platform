"""
Async repository helpers for SI ERP connections.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core_platform.data_management.models.si_erp_connection import (
    SIERPConnection,
    SIERPConnectionStatus,
)


def _to_uuid(value: Optional[Any]) -> Optional[UUID]:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return uuid.UUID(str(value))


def _normalize_status(value: Optional[Any]) -> SIERPConnectionStatus:
    if isinstance(value, SIERPConnectionStatus):
        return value
    if value is None:
        return SIERPConnectionStatus.CONFIGURED
    return SIERPConnectionStatus(str(value))


def _ensure_mapping(value: Optional[Any]) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _serialize(row: SIERPConnection) -> Dict[str, Any]:
    return {
        "connection_id": str(row.id),
        "organization_id": str(row.organization_id),
        "owner_user_id": str(row.owner_user_id) if row.owner_user_id else None,
        "erp_system": row.erp_system,
        "connection_name": row.connection_name,
        "environment": row.environment,
        "status": row.status.value if row.status else None,
        "status_reason": row.status_reason,
        "is_active": bool(row.is_active),
        "connection_config": row.connection_config or {},
        "metadata": row.extra_metadata or {},
        "last_status_at": row.last_status_at,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }


async def create_connection(
    db: AsyncSession,
    *,
    connection_id: Optional[str],
    organization_id: str,
    erp_system: str,
    connection_name: str,
    environment: str,
    connection_config: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    owner_user_id: Optional[str] = None,
    status: Optional[str] = None,
    status_reason: Optional[str] = None,
) -> Dict[str, Any]:
    row = SIERPConnection(
        id=_to_uuid(connection_id) or uuid.uuid4(),
        organization_id=_to_uuid(organization_id),
        owner_user_id=_to_uuid(owner_user_id),
        erp_system=erp_system,
        connection_name=connection_name,
        environment=environment or "sandbox",
        status=_normalize_status(status),
        status_reason=status_reason,
        connection_config=_ensure_mapping(connection_config),
        extra_metadata=_ensure_mapping(metadata),
        last_status_at=datetime.utcnow(),
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _serialize(row)


async def list_connections(
    db: AsyncSession,
    *,
    organization_id: Optional[str] = None,
    erp_system: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    stmt = select(SIERPConnection)
    if organization_id:
        stmt = stmt.where(SIERPConnection.organization_id == _to_uuid(organization_id))
    if erp_system:
        stmt = stmt.where(SIERPConnection.erp_system == erp_system)
    if status:
        stmt = stmt.where(SIERPConnection.status == _normalize_status(status))
    stmt = stmt.order_by(SIERPConnection.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [_serialize(r) for r in rows]


async def get_connection(db: AsyncSession, connection_id: str) -> Optional[Dict[str, Any]]:
    row = await db.get(SIERPConnection, _to_uuid(connection_id))
    return _serialize(row) if row else None


async def update_connection(
    db: AsyncSession,
    connection_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    row = await db.get(SIERPConnection, _to_uuid(connection_id))
    if not row:
        return None

    if "connection_name" in updates and updates["connection_name"]:
        row.connection_name = str(updates["connection_name"])
    if "environment" in updates and updates["environment"]:
        row.environment = str(updates["environment"])
    if "status" in updates and updates["status"]:
        row.status = _normalize_status(updates["status"])
        row.last_status_at = datetime.utcnow()
    if "status_reason" in updates:
        row.status_reason = updates["status_reason"]
    if "owner_user_id" in updates:
        row.owner_user_id = _to_uuid(updates["owner_user_id"])
    if "is_active" in updates:
        row.is_active = bool(updates["is_active"])
    if "connection_config" in updates and isinstance(updates["connection_config"], dict):
        merged = dict(row.connection_config or {})
        merged.update(updates["connection_config"])
        row.connection_config = merged
    if "metadata" in updates and isinstance(updates["metadata"], dict):
        merged_meta = dict(row.extra_metadata or {})
        merged_meta.update(updates["metadata"])
        row.extra_metadata = merged_meta

    await db.commit()
    await db.refresh(row)
    return _serialize(row)


async def delete_connection(db: AsyncSession, connection_id: str) -> Optional[Dict[str, Any]]:
    row = await db.get(SIERPConnection, _to_uuid(connection_id))
    if not row:
        return None
    payload = _serialize(row)
    await db.delete(row)
    await db.commit()
    return payload
