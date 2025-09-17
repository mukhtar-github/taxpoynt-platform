"""
Async repository for reconciliation configs.
"""
from __future__ import annotations

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from core_platform.data_management.models.reconciliation import ReconciliationConfig


async def save_config(db: AsyncSession, *, si_id: str, organization_id: Optional[str], config: Dict[str, Any]) -> Dict[str, Any]:
    row = ReconciliationConfig(
        si_id=UUID(si_id) if isinstance(si_id, str) else si_id,
        organization_id=UUID(organization_id) if organization_id and isinstance(organization_id, str) else organization_id,
        config=config,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"id": str(row.id), "si_id": str(row.si_id), "organization_id": str(row.organization_id) if row.organization_id else None, "config": row.config}


async def get_config(db: AsyncSession, *, si_id: str, organization_id: Optional[str]) -> Optional[Dict[str, Any]]:
    stmt = select(ReconciliationConfig).where(ReconciliationConfig.si_id == UUID(si_id) if isinstance(si_id, str) else si_id)
    if organization_id:
        stmt = stmt.where(ReconciliationConfig.organization_id == (UUID(organization_id) if isinstance(organization_id, str) else organization_id))
    row = (await db.execute(stmt.order_by(ReconciliationConfig.created_at.desc()))).scalars().first()
    if not row:
        return None
    return {"id": str(row.id), "si_id": str(row.si_id), "organization_id": str(row.organization_id) if row.organization_id else None, "config": row.config}


async def update_config(db: AsyncSession, *, si_id: str, organization_id: Optional[str], updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    current = await get_config(db, si_id=si_id, organization_id=organization_id)
    if not current:
        return None
    # Simple merge and save new row version (append-only)
    cfg = dict(current.get("config") or {})
    cfg.update(updates)
    return await save_config(db, si_id=si_id, organization_id=organization_id, config=cfg)

