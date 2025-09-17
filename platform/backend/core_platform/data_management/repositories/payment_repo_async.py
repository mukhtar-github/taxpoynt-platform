"""
Async repository for payment processor connections and webhooks.
"""
from __future__ import annotations

from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from core_platform.data_management.models.payment import (
    PaymentConnection, PaymentConnectionStatus, PaymentProvider,
    PaymentWebhook,
)


async def create_connection(
    db: AsyncSession,
    *,
    si_id: str,
    organization_id: Optional[str],
    provider: str,
    provider_connection_id: Optional[str] = None,
    status: str = "pending",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row = PaymentConnection(
        si_id=UUID(si_id) if isinstance(si_id, str) else si_id,
        organization_id=UUID(organization_id) if organization_id and isinstance(organization_id, str) else organization_id,
        provider=PaymentProvider(provider),
        provider_connection_id=provider_connection_id,
        status=PaymentConnectionStatus(status),
        connection_metadata=metadata or {},
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_dict(row)


async def get_connection(db: AsyncSession, connection_id: str) -> Optional[Dict[str, Any]]:
    row = (await db.execute(select(PaymentConnection).where(PaymentConnection.id == UUID(connection_id)))).scalars().first()
    return _to_dict(row) if row else None


async def list_connections(db: AsyncSession, *, si_id: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
    stmt = select(PaymentConnection)
    if si_id:
        stmt = stmt.where(PaymentConnection.si_id == UUID(si_id) if isinstance(si_id, str) else si_id)
    if provider:
        stmt = stmt.where(PaymentConnection.provider == PaymentProvider(provider))
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_to_dict(r) for r in rows], "count": len(rows)}


async def update_connection(db: AsyncSession, connection_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    row = (await db.execute(select(PaymentConnection).where(PaymentConnection.id == UUID(connection_id)))).scalars().first()
    if not row:
        return None
    for key in ("status", "account_reference", "connection_metadata"):
        if key in updates:
            setattr(row, key, updates[key])
    await db.commit()
    return _to_dict(row)


async def delete_connection(db: AsyncSession, connection_id: str) -> bool:
    await db.execute(delete(PaymentConnection).where(PaymentConnection.id == UUID(connection_id)))
    await db.commit()
    return True


async def register_webhook(db: AsyncSession, *, si_id: str, provider: str, endpoint_url: str, connection_id: Optional[str] = None, secret: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    row = PaymentWebhook(
        si_id=UUID(si_id) if isinstance(si_id, str) else si_id,
        provider=PaymentProvider(provider),
        endpoint_url=endpoint_url,
        secret=secret,
        connection_id=UUID(connection_id) if connection_id and isinstance(connection_id, str) else connection_id,
        webhook_metadata=metadata or {},
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _webhook_to_dict(row)


async def list_webhooks(db: AsyncSession, *, si_id: str, provider: Optional[str] = None) -> Dict[str, Any]:
    stmt = select(PaymentWebhook).where(PaymentWebhook.si_id == UUID(si_id) if isinstance(si_id, str) else si_id)
    if provider:
        stmt = stmt.where(PaymentWebhook.provider == PaymentProvider(provider))
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_webhook_to_dict(r) for r in rows], "count": len(rows)}


def _to_dict(r: PaymentConnection) -> Dict[str, Any]:
    return {
        "id": str(r.id),
        "si_id": str(r.si_id),
        "organization_id": str(r.organization_id) if r.organization_id else None,
        "provider": r.provider.value if r.provider else None,
        "provider_connection_id": r.provider_connection_id,
        "status": r.status.value if r.status else None,
        "account_reference": r.account_reference,
        "connection_metadata": r.connection_metadata or {},
    }


def _webhook_to_dict(r: PaymentWebhook) -> Dict[str, Any]:
    return {
        "id": str(r.id),
        "si_id": str(r.si_id),
        "provider": r.provider.value if r.provider else None,
        "endpoint_url": r.endpoint_url,
        "is_active": r.is_active,
        "connection_id": str(r.connection_id) if r.connection_id else None,
        "webhook_metadata": r.webhook_metadata or {},
    }

