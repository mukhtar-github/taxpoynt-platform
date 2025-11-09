"""Async repository for onboarding state persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import os

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.onboarding_state import OnboardingStateORM

_DEFAULT_PACKAGE_FLOWS: Dict[str, list[str]] = {
    "si": ["service-selection", "company-profile", "system-connectivity", "review", "launch"],
    "app": ["service-selection", "company-profile", "system-connectivity", "launch"],
    "hybrid": ["service-selection", "company-profile", "system-connectivity", "review", "launch"],
}

_DEFAULT_STEP_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "service-selection": {
        "title": "Select Your Service Focus",
        "description": "Choose how you plan to use TaxPoynt so we can tailor the workspace.",
        "success_criteria": "Primary service package confirmed",
    },
    "company-profile": {
        "title": "Company Profile",
        "description": "Confirm the organisation details we will use across compliance and billing.",
        "success_criteria": "Company base profile captured",
    },
    "system-connectivity": {
        "title": "Connect Systems",
        "description": "Link the ERP, CRM, or banking systems needed for automation.",
        "success_criteria": "At least one connector configured",
    },
    "review": {
        "title": "Review & Confirm",
        "description": "Double-check your selections before launch.",
        "success_criteria": "Launch checklist acknowledged",
    },
    "launch": {
        "title": "Launch Workspace",
        "description": "Activate the workspace and unlock the SI dashboard.",
        "success_criteria": "Workspace activated",
    },
}

_ALLOWED_WIZARD_SECTIONS = {"company_profile", "service_focus"}

_DEMO_TRUE_VALUES = {"1", "true", "yes", "on"}


def _is_demo_mode() -> bool:
    return os.getenv("DEMO_MODE", "false").strip().lower() in _DEMO_TRUE_VALUES


class OnboardingStateRepositoryAsync:
    """Repository for CRUD operations on onboarding states."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def fetch_state(self, user_id: str) -> Optional[OnboardingStateORM]:
        result = await self._session.execute(
            select(OnboardingStateORM).where(OnboardingStateORM.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def ensure_state(self, user_id: str, service_package: str) -> OnboardingStateORM:
        """Ensure an onboarding state exists for the user, initializing if required."""
        record = await self.fetch_state(user_id)
        if record:
            return record

        normalized_package = (service_package or "si").lower()
        package = normalized_package if normalized_package in _DEFAULT_PACKAGE_FLOWS else "si"
        steps = _DEFAULT_PACKAGE_FLOWS[package]
        now = datetime.now(timezone.utc)
        metadata: Dict[str, Any] = {
            "service_package": package,
            "expected_steps": steps,
            "step_definitions": {
                step: _DEFAULT_STEP_DEFINITIONS.get(
                    step, {"title": step, "description": "", "success_criteria": ""}
                )
                for step in steps
            },
        }

        if _is_demo_mode():
            demo_timestamp = now.isoformat()
            metadata.setdefault("banking_connections", {}).setdefault(
                "mono",
                {
                    "status": "demo",
                    "bankName": "Demo Bank",
                    "lastMessage": "Demo feed active",
                    "lastUpdated": demo_timestamp,
                },
            )
            metadata.setdefault("erp_connections", {}).setdefault(
                "odoo",
                {
                    "status": "demo",
                    "connectionName": "Demo Odoo Workspace",
                    "lastMessage": "Demo workspace configured",
                    "lastTestAt": demo_timestamp,
                },
            )

        record = OnboardingStateORM(
            user_id=user_id,
            service_package=package,
            current_step=steps[0] if steps else "service-selection",
            completed_steps=[],
            has_started=False,
            is_complete=False,
            state_metadata=metadata,
            created_at=now,
            updated_at=now,
            last_active_date=now,
        )
        return await self.persist(record)

    async def persist(self, record: OnboardingStateORM) -> OnboardingStateORM:
        """Persist the provided record, returning the refreshed instance."""
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def upsert_wizard_section(
        self,
        user_id: str,
        service_package: str,
        *,
        section: str,
        payload: Dict[str, Any],
        current_step: Optional[str] = None,
    ) -> OnboardingStateORM:
        """Merge wizard metadata for the provided section while preserving other data."""
        if section not in _ALLOWED_WIZARD_SECTIONS:
            raise ValueError(f"Unsupported wizard section '{section}'")

        record = await self.ensure_state(user_id, service_package)

        metadata = dict(record.state_metadata or {})
        wizard = dict(metadata.get("wizard") or {})
        wizard[section] = payload
        metadata["wizard"] = wizard

        metadata.setdefault("service_package", record.service_package)
        record.state_metadata = metadata
        record.has_started = True

        now = datetime.now(timezone.utc)
        record.last_active_date = now
        record.updated_at = now

        if current_step:
            record.current_step = current_step

        return await self.persist(record)

    async def delete_state(self, user_id: str) -> None:
        await self._session.execute(
            delete(OnboardingStateORM).where(OnboardingStateORM.user_id == user_id)
        )
        await self._session.commit()
