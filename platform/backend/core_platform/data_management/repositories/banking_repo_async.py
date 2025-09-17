"""
Async Banking Repositories
==========================

Lightweight async helpers to persist and query banking integration state.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from core_platform.data_management.models.banking import (
    BankingConnection,
    BankAccount,
    BankTransaction,
    BankingProvider,
    ConnectionStatus,
)


async def create_banking_connection(
    db: AsyncSession,
    *,
    si_id: str,
    organization_id: Optional[str],
    provider: str,
    provider_connection_id: str,
    status: str = "pending",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    conn = BankingConnection(
        si_id=UUID(si_id) if isinstance(si_id, str) else si_id,
        organization_id=UUID(organization_id) if organization_id and isinstance(organization_id, str) else organization_id,
        provider=BankingProvider(provider),
        provider_connection_id=provider_connection_id,
        status=ConnectionStatus(status),
        connection_metadata=metadata or {},
    )
    db.add(conn)
    await db.flush()
    return _connection_to_dict(conn)


async def get_banking_connection(db: AsyncSession, connection_id: str) -> Optional[Dict[str, Any]]:
    res = await db.execute(select(BankingConnection).where(BankingConnection.id == UUID(connection_id)))
    row = res.scalars().first()
    return _connection_to_dict(row) if row else None


async def list_banking_connections(
    db: AsyncSession,
    *,
    si_id: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    stmt = select(BankingConnection)
    if si_id:
        stmt = stmt.where(BankingConnection.si_id == UUID(si_id) if isinstance(si_id, str) else si_id)
    if provider:
        stmt = stmt.where(BankingConnection.provider == BankingProvider(provider))
    total = len((await db.execute(stmt)).scalars().all())
    rows = (await db.execute(stmt.offset(offset).limit(limit))).scalars().all()
    return {
        "items": [_connection_to_dict(r) for r in rows],
        "count": total,
        "limit": limit,
        "offset": offset,
    }


async def update_banking_connection(
    db: AsyncSession,
    connection_id: str,
    updates: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    res = await db.execute(select(BankingConnection).where(BankingConnection.id == UUID(connection_id)))
    row = res.scalars().first()
    if not row:
        return None
    for k, v in updates.items():
        if hasattr(row, k):
            setattr(row, k, v)
    await db.flush()
    return _connection_to_dict(row)


async def delete_banking_connection(db: AsyncSession, connection_id: str) -> bool:
    await db.execute(delete(BankingConnection).where(BankingConnection.id == UUID(connection_id)))
    return True


def _connection_to_dict(c: BankingConnection) -> Dict[str, Any]:
    return {
        "id": str(c.id),
        "si_id": str(c.si_id),
        "organization_id": str(c.organization_id) if c.organization_id else None,
        "provider": c.provider.value if c.provider else None,
        "provider_connection_id": c.provider_connection_id,
        "status": c.status.value if c.status else None,
        "bank_name": c.bank_name,
        "account_number": c.account_number,
        "account_name": c.account_name,
        "account_type": c.account_type.value if c.account_type else None,
        "connection_metadata": c.connection_metadata or {},
        "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
    }

