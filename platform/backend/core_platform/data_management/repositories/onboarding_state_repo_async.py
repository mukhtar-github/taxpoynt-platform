"""Async repository for onboarding state persistence."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.onboarding_state import OnboardingStateORM


class OnboardingStateRepositoryAsync:
    """Repository for CRUD operations on onboarding states."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_state(self, user_id: str) -> Optional[OnboardingStateORM]:
        result = await self._session.execute(
            select(OnboardingStateORM).where(OnboardingStateORM.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def persist(self, record: OnboardingStateORM) -> OnboardingStateORM:
        """Persist the provided record, returning the refreshed instance."""
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def delete_state(self, user_id: str) -> None:
        await self._session.execute(
            delete(OnboardingStateORM).where(OnboardingStateORM.user_id == user_id)
        )
        await self._session.commit()
