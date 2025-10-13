"""
SI Onboarding Service
====================

Persisted onboarding state management for System Integrator, APP, and Hybrid
users. Stores progress in the database (async) with a short-lived in-memory
cache to avoid repeated queries during rapid wizard interactions.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select

from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.onboarding_state import OnboardingStateORM
from core_platform.data_management.models.firs_submission import FIRSSubmission, SubmissionStatus
from core_platform.data_management.models.integration import Integration, IntegrationStatus
from core_platform.data_management.models.user import User
from core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)
from core_platform.utils.irn_helper import (
    IRNGenerationError,
    generate_canonical_irn,
)

logger = logging.getLogger(__name__)


@dataclass
class OnboardingState:
    user_id: str
    service_package: str
    current_step: str
    completed_steps: List[str]
    has_started: bool
    is_complete: bool
    last_active_date: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class SIOnboardingService:
    """Persisted onboarding service used by the message router."""

    _CACHE_TTL_SECONDS = 60

    STEP_DEFINITIONS: Dict[str, Dict[str, Any]] = {
        "service-selection": {
            "title": "Select Your Service Focus",
            "description": "Choose how you plan to use TaxPoynt so we can tailor the workspace.",
            "success_criteria": "Primary service package confirmed",
        },
        "company-profile": {
            "title": "Company Profile",
            "description": "Confirm the organisation details we will use across compliance and billing.",
            "success_criteria": "Company name and region on file",
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

    PACKAGE_FLOWS: Dict[str, List[str]] = {
        "si": [
            "service-selection",
            "company-profile",
            "system-connectivity",
            "review",
            "launch",
        ],
        "app": [
            "service-selection",
            "company-profile",
            "system-connectivity",
            "launch",
        ],
        "hybrid": [
            "service-selection",
            "company-profile",
            "system-connectivity",
            "review",
            "launch",
        ],
    }

    def __init__(self) -> None:
        self.service_name = "SI Onboarding Service"
        self.version = "2.1.0"

        self.default_steps = self.PACKAGE_FLOWS

        self._state_cache: Dict[str, Tuple[datetime, OnboardingState]] = {}
        self._cache_ttl = timedelta(seconds=self._CACHE_TTL_SECONDS)

        logger.info("%s v%s initialized", self.service_name, self.version)

    # ------------------------------------------------------------------
    # Public entry point (invoked by message router)
    # ------------------------------------------------------------------
    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async for session in get_async_session():
                repo = OnboardingStateRepositoryAsync(session)
                return await self._handle_with_repo(repo, operation, payload)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Onboarding operation failed %s: %s", operation, exc, exc_info=True)
            raise RuntimeError(f"Onboarding operation failed: {exc}")

    async def _handle_with_repo(
        self,
        repo: OnboardingStateRepositoryAsync,
        operation: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("User ID is required for onboarding operations")

        service_package = self._normalize_service_package(payload.get("service_package"))

        if operation == "get_onboarding_state":
            return await self._handle_get_onboarding_state(repo, user_id, service_package)
        if operation == "update_onboarding_state":
            return await self._handle_update_onboarding_state(repo, user_id, payload, service_package)
        if operation == "complete_onboarding_step":
            return await self._handle_complete_onboarding_step(repo, user_id, payload, service_package)
        if operation == "complete_onboarding":
            return await self._handle_complete_onboarding(repo, user_id, payload, service_package)
        if operation == "reset_onboarding_state":
            return await self._handle_reset_onboarding_state(repo, user_id)
        if operation == "get_onboarding_analytics":
            return await self._handle_get_onboarding_analytics(repo, user_id, service_package)
        if operation == "initiate_organization_onboarding":
            org_id = payload.get("org_id")
            return {"operation": operation, "success": True, "organization_id": org_id, "initiated": True}
        if operation == "get_organization_onboarding_status":
            org_id = payload.get("org_id")
            return {"operation": operation, "success": True, "organization_id": org_id, "status": "pending"}

        raise ValueError(f"Unknown onboarding operation: {operation}")

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    async def _handle_get_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        service_package: str,
    ) -> Dict[str, Any]:
        state = await self._get_onboarding_state(repo, user_id, service_package)
        payload = self._state_with_progress(state)

        runtime = await self._build_runtime_metadata(repo, state, service_package)
        if runtime:
            metadata = payload.get("metadata") or {}
            metadata.update(runtime)
            payload["metadata"] = metadata

        return {
            "operation": "get_onboarding_state",
            "success": True,
            "data": payload,
            "user_id": user_id,
        }

    async def _handle_update_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        payload: Dict[str, Any],
        service_package: str,
    ) -> Dict[str, Any]:
        onboarding_data = payload.get("onboarding_data", {})
        current_step = onboarding_data.get("current_step")
        if not current_step:
            raise ValueError("Current step is required for onboarding state update")

        completed_steps = onboarding_data.get("completed_steps") or []
        metadata = onboarding_data.get("metadata") or {}

        state = await self._update_onboarding_state(
            repo,
            user_id,
            current_step=current_step,
            additional_completed_steps=completed_steps,
            metadata_updates=metadata,
            service_package=service_package,
        )

        return {
            "operation": "update_onboarding_state",
            "success": True,
            "data": self._state_with_progress(state),
            "user_id": user_id,
        }

    async def _handle_complete_onboarding_step(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        payload: Dict[str, Any],
        service_package: str,
    ) -> Dict[str, Any]:
        step_name = payload.get("step_name")
        if not step_name:
            raise ValueError("Step name is required to complete onboarding step")

        metadata = payload.get("metadata") or {}
        state = await self._complete_step(
            repo,
            user_id,
            step_name=step_name,
            metadata_updates=metadata,
            service_package=service_package,
        )

        return {
            "operation": "complete_onboarding_step",
            "success": True,
            "data": self._state_with_progress(state),
            "step_completed": step_name,
            "user_id": user_id,
        }

    async def _handle_complete_onboarding(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        payload: Dict[str, Any],
        service_package: str,
    ) -> Dict[str, Any]:
        metadata = payload.get("metadata") or {}
        state = await self._complete_onboarding(
            repo,
            user_id,
            completion_metadata=metadata,
            service_package=service_package,
        )

        return {
            "operation": "complete_onboarding",
            "success": True,
            "data": self._state_with_progress(state),
            "user_id": user_id,
            "completed_at": state.metadata.get("completion", {}).get("completed_at"),
        }

    async def _handle_reset_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        await repo.delete_state(user_id)
        self._invalidate_cache(user_id)

        return {
            "operation": "reset_onboarding_state",
            "success": True,
            "message": "Onboarding state reset successfully",
            "user_id": user_id,
        }

    async def _handle_get_onboarding_analytics(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        service_package: str,
    ) -> Dict[str, Any]:
        analytics = await self._get_onboarding_analytics(repo, user_id, service_package)
        return {
            "operation": "get_onboarding_analytics",
            "success": True,
            "data": analytics,
            "user_id": user_id,
        }

    # ------------------------------------------------------------------
    # Core persistence helpers
    # ------------------------------------------------------------------
    async def _get_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        service_package: Optional[str],
    ) -> OnboardingState:
        cached = self._get_cached_state(user_id)
        if cached:
            return cached

        record = await self._get_state_record(repo, user_id, service_package)
        state = self._from_orm(record)
        self._cache_state(user_id, state)
        return state

    async def _update_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        *,
        current_step: str,
        additional_completed_steps: List[str],
        metadata_updates: Dict[str, Any],
        service_package: Optional[str],
    ) -> OnboardingState:
        record = await self._get_state_record(repo, user_id, service_package)

        record.current_step = current_step
        record.completed_steps = self._merge_completed_steps(
            record.completed_steps or [], additional_completed_steps
        )
        record.has_started = True
        record.is_complete = record.is_complete or "launch" in record.completed_steps
        record.service_package = service_package or record.service_package
        merged_metadata = dict(record.state_metadata or {})
        merged_metadata.setdefault("service_package", record.service_package)
        if metadata_updates:
            merged_metadata.update(metadata_updates)
        record.state_metadata = self._ensure_metadata_consistency(
            merged_metadata,
            record.service_package,
        )

        now = self._utc_now()
        record.last_active_date = now
        record.updated_at = now

        persisted = await repo.persist(record)
        state = self._from_orm(persisted)
        self._cache_state(user_id, state)
        return state

    async def _complete_step(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        *,
        step_name: str,
        metadata_updates: Dict[str, Any],
        service_package: Optional[str],
    ) -> OnboardingState:
        record = await self._get_state_record(repo, user_id, service_package)

        record.completed_steps = self._merge_completed_steps(
            record.completed_steps or [], [step_name]
        )
        record.current_step = step_name
        record.has_started = True
        record.is_complete = record.is_complete or step_name == "launch"

        metadata = dict(record.state_metadata or {})
        metadata.setdefault("service_package", record.service_package)
        if metadata_updates:
            step_metadata = metadata.setdefault("step_metadata", {})
            step_metadata[step_name] = {
                **metadata_updates,
                "completed_at": self._isoformat(self._utc_now()),
            }
        record.state_metadata = self._ensure_metadata_consistency(
            metadata,
            record.service_package,
        )

        now = self._utc_now()
        record.last_active_date = now
        record.updated_at = now

        persisted = await repo.persist(record)
        state = self._from_orm(persisted)
        self._cache_state(user_id, state)
        return state

    async def _complete_onboarding(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        *,
        completion_metadata: Dict[str, Any],
        service_package: Optional[str],
    ) -> OnboardingState:
        state = await self._complete_step(
            repo,
            user_id,
            step_name="launch",
            metadata_updates=completion_metadata,
            service_package=service_package,
        )

        record = await self._get_state_record(repo, user_id, service_package)
        metadata = dict(record.state_metadata or {})
        metadata.setdefault("service_package", record.service_package)
        completion_section = metadata.setdefault("completion", {})
        completion_section.update(completion_metadata)
        completion_section.setdefault("completed_at", self._isoformat(self._utc_now()))

        record.state_metadata = self._ensure_metadata_consistency(
            metadata,
            record.service_package,
        )
        record.is_complete = True
        record.current_step = "launch"
        record.last_active_date = self._utc_now()
        record.updated_at = record.last_active_date

        persisted = await repo.persist(record)
        final_state = self._from_orm(persisted)
        self._cache_state(user_id, final_state)
        logger.info("Onboarding completed for user %s", user_id)
        return final_state

    async def _get_onboarding_analytics(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        service_package: Optional[str],
    ) -> Dict[str, Any]:
        state = await self._get_onboarding_state(repo, user_id, service_package)

        expected_steps = state.metadata.get("expected_steps", [])
        total_count = len(expected_steps)
        completed_count = len(state.completed_steps)
        completion_percentage = (completed_count / total_count * 100) if total_count else 0

        created_at = self._parse_iso(state.created_at)
        last_active = self._parse_iso(state.last_active_date)
        now = self._utc_now()
        days_since_start = (now - created_at).days
        days_since_last_active = (now - last_active).days

        remaining_steps = [step for step in expected_steps if step not in state.completed_steps]

        return {
            "user_id": user_id,
            "status": "complete" if state.is_complete else "in_progress" if state.has_started else "not_started",
            "analytics": {
                "completion_percentage": round(completion_percentage, 1),
                "completed_steps": completed_count,
                "total_steps": total_count,
                "remaining_steps": len(remaining_steps),
                "current_step": state.current_step,
                "days_since_start": days_since_start,
                "days_since_last_active": days_since_last_active,
                "is_stale": days_since_last_active > 7,
                "expected_completion": {
                    "next_steps": remaining_steps,
                    "estimated_remaining_time": f"{max(0, len(remaining_steps))} steps remaining",
                },
            },
            "timeline": {
                "started_at": state.created_at,
                "last_active": state.last_active_date,
                "completed_at": state.metadata.get("completion", {}).get("completed_at") if state.is_complete else None,
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _get_state_record(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        service_package: Optional[str],
    ) -> OnboardingStateORM:
        record = await repo.fetch_state(user_id)
        if record is None:
            record = await self._create_state_record(repo, user_id, service_package)
        elif service_package and record.service_package != service_package:
            metadata = dict(record.state_metadata or {})
            metadata["service_package"] = service_package
            record.service_package = service_package
            record.state_metadata = self._ensure_metadata_consistency(
                metadata,
                record.service_package,
            )
            record = await repo.persist(record)
            self._invalidate_cache(user_id)
        return record

    async def _create_state_record(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        service_package: Optional[str],
    ) -> OnboardingStateORM:
        package = self._normalize_service_package(service_package)
        now = self._utc_now()
        expected_steps = self.default_steps.get(package, self.default_steps["si"])
        metadata: Dict[str, Any] = {
            "service_package": package,
            "initialization_date": self._isoformat(now),
            "expected_steps": expected_steps,
            "step_definitions": {
                step: self.STEP_DEFINITIONS.get(step, {"title": step, "description": "", "success_criteria": ""})
                for step in expected_steps
            },
        }
        metadata = self._ensure_metadata_consistency(metadata, package)

        record = OnboardingStateORM(
            user_id=user_id,
            service_package=package,
            current_step=expected_steps[0] if expected_steps else "service-selection",
            completed_steps=[],
            has_started=False,
            is_complete=False,
            state_metadata=metadata,
            created_at=now,
            updated_at=now,
            last_active_date=now,
        )

        persisted = await repo.persist(record)
        state = self._from_orm(persisted)
        self._cache_state(user_id, state)
        logger.info("Initialized onboarding state for user %s", user_id)
        return persisted

    def _state_with_progress(self, state: OnboardingState) -> Dict[str, Any]:
        data = asdict(state)
        data["progress"] = self._calculate_progress(state)
        return data

    async def _build_runtime_metadata(
        self,
        repo: OnboardingStateRepositoryAsync,
        state: OnboardingState,
        service_package: str,
    ) -> Dict[str, Any]:
        session = getattr(repo, "_session", None)
        if session is None:
            return {}

        runtime: Dict[str, Any] = {}

        user = await session.get(User, uuid.UUID(state.user_id)) if self._is_uuid(state.user_id) else None
        if user:
            runtime["login_count"] = user.login_count or 0

        organization_id = getattr(user, "organization_id", None) if user else None
        if organization_id:
            connections = await session.execute(
                select(Integration).where(Integration.organization_id == organization_id).order_by(Integration.last_sync_at.desc().nullslast())
            )
            integration_rows = list(connections.scalars())

            runtime["connections"] = {
                "total": len(integration_rows),
                "active": sum(1 for item in integration_rows if item.status == IntegrationStatus.ACTIVE),
                "failing": sum(1 for item in integration_rows if item.status == IntegrationStatus.FAILED),
                "items": [
                    {
                        "id": str(item.id),
                        "name": item.name,
                        "type": item.integration_type.value,
                        "status": item.status.value,
                        "lastSync": self._format_optional_datetime(item.last_sync_at),
                        "error": item.last_error,
                        "needsAttention": item.needs_attention,
                    }
                    for item in integration_rows[:5]
                ],
            }

            submissions_stmt = (
                select(FIRSSubmission)
                .where(FIRSSubmission.organization_id == organization_id)
                .order_by(FIRSSubmission.created_at.desc())
                .limit(5)
            )
            submission_rows = await session.execute(submissions_stmt)
            submissions = list(submission_rows.scalars())
            runtime["irn_progress"] = {
                "total_generated": sum(
                    1
                    for item in submissions
                    if item.status in (SubmissionStatus.SUBMITTED, SubmissionStatus.ACCEPTED)
                ),
                "pending": sum(
                    1
                    for item in submissions
                    if item.status in (SubmissionStatus.PENDING, SubmissionStatus.PROCESSING)
                ),
                "recent": [
                    {
                        "irn": item.irn,
                        "status": item.status.value,
                        "created_at": self._format_optional_datetime(item.created_at),
                    }
                    for item in submissions
                ],
            }

        if runtime:
            return {"runtime": runtime}
        return {}

    @staticmethod
    def _is_uuid(value: str) -> bool:
        try:
            uuid.UUID(str(value))
            return True
        except Exception:
            return False

    @staticmethod
    def _format_optional_datetime(value: Optional[datetime]) -> Optional[str]:
        if not value:
            return None
        return value.replace(microsecond=0).isoformat() + "Z"

    def _ensure_metadata_consistency(
        self,
        metadata: Dict[str, Any],
        service_package: str,
    ) -> Dict[str, Any]:
        expected_steps = self.default_steps.get(service_package, self.default_steps["si"])
        metadata["service_package"] = service_package
        metadata["expected_steps"] = expected_steps
        metadata["step_definitions"] = {
            step: self.STEP_DEFINITIONS.get(
                step, {"title": step, "description": "", "success_criteria": ""}
            )
            for step in expected_steps
        }
        return self._attach_irn_preview(metadata)

    def _attach_irn_preview(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Augment metadata with a canonical IRN preview for onboarding UI."""
        invoice_sources = [
            metadata.get("invoice_preview", {}).get("invoice_number"),
            metadata.get("invoice_preview", {}).get("invoiceNumber"),
            metadata.get("draft_invoice", {}).get("invoice_number") if isinstance(metadata.get("draft_invoice"), dict) else None,
            metadata.get("last_invoice_number"),
            "0001",
        ]
        service_sources = [
            metadata.get("company_profile", {}).get("firs_service_id") if isinstance(metadata.get("company_profile"), dict) else None,
            metadata.get("company_profile", {}).get("service_id") if isinstance(metadata.get("company_profile"), dict) else None,
            metadata.get("service_id"),
            metadata.get("service_package"),
            "SERVICE00",
        ]
        issued_sources = [
            metadata.get("invoice_preview", {}).get("issued_on"),
            metadata.get("invoice_preview", {}).get("issuedOn"),
            metadata.get("completion", {}).get("completed_at") if isinstance(metadata.get("completion"), dict) else None,
            metadata.get("last_active_date"),
            self._isoformat(self._utc_now()),
        ]

        invoice_number = next((value for value in invoice_sources if value), "0001")
        service_id = next((value for value in service_sources if value), "SERVICE00")
        issued_on = next((value for value in issued_sources if value), self._utc_now())

        try:
            metadata["irn_preview"] = generate_canonical_irn(
                invoice_number=invoice_number,
                service_id=service_id,
                issued_on=issued_on,
            )
        except IRNGenerationError:
            metadata["irn_preview"] = generate_canonical_irn("0001", "SERVICE", self._utc_now())

        return metadata

    def _calculate_progress(self, state: OnboardingState) -> Dict[str, Any]:
        expected_steps = state.metadata.get("expected_steps", [])
        total = len(expected_steps)
        completed = len(state.completed_steps)
        remaining = [step for step in expected_steps if step not in state.completed_steps]
        completion_rate = (completed / total * 100) if total else 0
        return {
            "completed": completed,
            "total": total,
            "completion_rate": round(completion_rate, 1),
            "remaining_steps": remaining,
            "current_step": state.current_step,
            "is_complete": state.is_complete,
        }

    def _from_orm(self, record: OnboardingStateORM) -> OnboardingState:
        return OnboardingState(
            user_id=record.user_id,
            service_package=record.service_package,
            current_step=record.current_step,
            completed_steps=list(record.completed_steps or []),
            has_started=record.has_started,
            is_complete=record.is_complete,
            last_active_date=self._isoformat(record.last_active_date),
            metadata=dict(record.state_metadata or {}),
            created_at=self._isoformat(record.created_at),
            updated_at=self._isoformat(record.updated_at),
        )

    def _merge_completed_steps(self, existing: List[str], new_steps: List[str]) -> List[str]:
        seen = set()
        merged: List[str] = []
        for step in existing + new_steps:
            if step not in seen:
                seen.add(step)
                merged.append(step)
        return merged

    def _normalize_service_package(self, value: Optional[str]) -> str:
        if value in {"si", "app", "hybrid"}:
            return value
        return "si"

    def _get_cached_state(self, user_id: str) -> Optional[OnboardingState]:
        entry = self._state_cache.get(user_id)
        if not entry:
            return None
        cached_at, state = entry
        if cached_at + self._cache_ttl < self._utc_now():
            self._state_cache.pop(user_id, None)
            return None
        return state

    def _cache_state(self, user_id: str, state: OnboardingState) -> None:
        self._state_cache[user_id] = (self._utc_now(), state)

    def _invalidate_cache(self, user_id: str) -> None:
        self._state_cache.pop(user_id, None)

    def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _isoformat(self, value: Optional[datetime]) -> str:
        if not value:
            value = self._utc_now()
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    def _parse_iso(self, value: str) -> datetime:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
