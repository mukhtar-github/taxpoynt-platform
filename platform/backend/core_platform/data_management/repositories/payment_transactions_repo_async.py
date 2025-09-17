"""
Async repository for payment transactions (unified view).
"""
from __future__ import annotations

from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core_platform.data_management.models.payment import PaymentTransaction, PaymentProvider


async def list_transactions_by_si(db: AsyncSession, *, si_id: str, limit: int = 100) -> Dict[str, Any]:
    # Join via connections
    from core_platform.data_management.models.payment import PaymentConnection
    stmt = (
        select(PaymentTransaction)
        .join(PaymentConnection, PaymentConnection.id == PaymentTransaction.connection_id)
        .where(PaymentConnection.si_id == (UUID(si_id) if isinstance(si_id, str) else si_id))
        .order_by(PaymentTransaction.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {"items": [_to_dict(r) for r in rows], "count": len(rows)}


def _to_dict(r: PaymentTransaction) -> Dict[str, Any]:
    return {
        "id": str(r.id),
        "connection_id": str(r.connection_id),
        "provider": r.provider.value if r.provider else None,
        "provider_transaction_id": r.provider_transaction_id,
        "amount": r.amount,
        "currency": r.currency,
        "status": r.status.value if r.status else None,
        "occurred_at": r.occurred_at.isoformat() if r.occurred_at else None,
        "transaction_metadata": r.transaction_metadata or {},
    }

