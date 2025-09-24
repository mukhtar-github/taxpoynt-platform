"""
Async repository helpers for the Participant registry (four-corner routing).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.models.network import Participant, ParticipantStatus


async def create_participant(
    session: AsyncSession,
    *,
    identifier: str,
    role: str,
    ap_endpoint_url: str,
    preferred_protocol: str = "http",
    organization_id: Optional[str] = None,
    public_key: Optional[str] = None,
    certificate_pem: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Participant:
    """Create a participant registry entry."""
    # Ensure no duplicate identifier
    existing = (await session.execute(select(Participant).where(Participant.identifier == identifier))).scalars().first()
    if existing:
        return existing
    row = Participant(
        identifier=identifier,
        role=role,
        ap_endpoint_url=ap_endpoint_url,
        preferred_protocol=preferred_protocol,
        organization_id=organization_id,  # type: ignore[arg-type]
        public_key=public_key,
        certificate_pem=certificate_pem,
        metadata_json=metadata or {},
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def get_participant_by_identifier(session: AsyncSession, identifier: str) -> Optional[Participant]:
    """Fetch a participant by external identifier (TIN/GLN)."""
    return (await session.execute(select(Participant).where(Participant.identifier == identifier))).scalars().first()


async def list_participants(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    role: Optional[str] = None,
    organization_id: Optional[str] = None,
) -> List[Participant]:
    """List participants with optional filters."""
    stmt = select(Participant)
    if status:
        stmt = stmt.where(Participant.status == status)
    if role:
        stmt = stmt.where(Participant.role == role)
    if organization_id:
        stmt = stmt.where(Participant.organization_id == organization_id)
    stmt = stmt.offset(offset).limit(limit)
    return (await session.execute(stmt)).scalars().all()


async def update_participant(
    session: AsyncSession,
    participant_id: UUID | str,
    updates: Dict[str, Any],
) -> Optional[Participant]:
    """Update participant fields and return the updated row."""
    row = (await session.execute(select(Participant).where(Participant.id == participant_id))).scalars().first()
    if not row:
        return None
    for key in [
        "ap_endpoint_url",
        "preferred_protocol",
        "public_key",
        "certificate_pem",
    ]:
        if key in updates:
            setattr(row, key, updates[key])
    if isinstance(updates.get("metadata"), dict):
        meta = getattr(row, "metadata_json", {}) or {}
        meta.update(updates["metadata"])
        row.metadata_json = meta
    if updates.get("status") in (ParticipantStatus.ACTIVE.value, ParticipantStatus.SUSPENDED.value):
        row.status = ParticipantStatus(updates["status"])  # type: ignore[assignment]
    await session.commit()
    await session.refresh(row)
    return row


async def deactivate_participant(session: AsyncSession, participant_id: UUID | str) -> bool:
    """Soft-deactivate a participant (sets status=suspended)."""
    row = (await session.execute(select(Participant).where(Participant.id == participant_id))).scalars().first()
    if not row:
        return False
    row.status = ParticipantStatus.SUSPENDED
    await session.commit()
    return True

