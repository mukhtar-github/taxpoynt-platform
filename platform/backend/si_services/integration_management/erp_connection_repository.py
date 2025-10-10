from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.repositories.si_erp_connection_repo_async import (
    create_connection as db_create_connection,
    list_connections as db_list_connections,
    get_connection as db_get_connection,
    update_connection as db_update_connection,
    delete_connection as db_delete_connection,
)


def _ensure_datetime(value: Optional[datetime]) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.now(timezone.utc)


@dataclass
class ERPConnectionRecord:
    """ERP connection data returned from the persistence layer."""

    connection_id: str
    organization_id: str
    erp_system: str
    connection_name: str
    environment: str
    connection_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: str = "configured"
    owner_user_id: Optional[str] = None
    status_reason: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_status_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ERPConnectionRecord":
        return cls(
            connection_id=payload["connection_id"],
            organization_id=payload["organization_id"],
            erp_system=payload["erp_system"],
            connection_name=payload["connection_name"],
            environment=payload["environment"],
            connection_config=dict(payload.get("connection_config") or {}),
            metadata=dict(payload.get("metadata") or {}),
            status=payload.get("status") or "configured",
            owner_user_id=payload.get("owner_user_id"),
            status_reason=payload.get("status_reason"),
            is_active=bool(payload.get("is_active", True)),
            created_at=_ensure_datetime(payload.get("created_at")),
            updated_at=_ensure_datetime(payload.get("updated_at")),
            last_status_at=payload.get("last_status_at"),
        )


class ERPConnectionRepository:
    """Async repository wrapper for ERP connections."""

    async def create(self, record: ERPConnectionRecord) -> ERPConnectionRecord:
        async for db in get_async_session():
            payload = await db_create_connection(
                db,
                connection_id=record.connection_id,
                organization_id=record.organization_id,
                erp_system=record.erp_system,
                connection_name=record.connection_name,
                environment=record.environment,
                connection_config=record.connection_config,
                metadata=record.metadata,
                owner_user_id=record.owner_user_id,
                status=record.status,
                status_reason=record.status_reason,
            )
            return ERPConnectionRecord.from_dict(payload)
        raise RuntimeError("Failed to acquire database session for ERP connection creation")

    async def list(
        self,
        *,
        organization_id: Optional[str] = None,
        erp_system: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ERPConnectionRecord]:
        async for db in get_async_session():
            rows = await db_list_connections(
                db,
                organization_id=organization_id,
                erp_system=erp_system,
                status=status,
            )
            return [ERPConnectionRecord.from_dict(row) for row in rows]
        return []

    async def get(self, connection_id: str) -> Optional[ERPConnectionRecord]:
        async for db in get_async_session():
            payload = await db_get_connection(db, connection_id)
            return ERPConnectionRecord.from_dict(payload) if payload else None
        return None

    async def update(self, connection_id: str, updates: Dict[str, Any]) -> Optional[ERPConnectionRecord]:
        async for db in get_async_session():
            payload = await db_update_connection(db, connection_id, updates)
            return ERPConnectionRecord.from_dict(payload) if payload else None
        return None

    async def delete(self, connection_id: str) -> Optional[ERPConnectionRecord]:
        async for db in get_async_session():
            payload = await db_delete_connection(db, connection_id)
            return ERPConnectionRecord.from_dict(payload) if payload else None
        return None
