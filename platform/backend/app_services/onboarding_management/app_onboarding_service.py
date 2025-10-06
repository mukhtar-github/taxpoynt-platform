"""
APP Onboarding Service
=====================

Service for handling onboarding state management operations for Access Point Providers.
Provides centralized onboarding progress tracking, state synchronization, and analytics
specific to APP users.

Operations Handled:
- get_onboarding_state
- update_onboarding_state  
- complete_onboarding_step
- complete_onboarding
- reset_onboarding_state
- get_onboarding_analytics
- get_business_verification_status
- get_firs_integration_status

Architecture:
- Follows APP service patterns
- Handles message router operations
- Provides database persistence for APP onboarding state
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from core_platform.services.analytics_service import OnboardingAnalyticsService
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)
from core_platform.data_management.models.onboarding_state import (
    OnboardingStateORM,
    serialize_completed_steps,
)

logger = logging.getLogger(__name__)


@dataclass
class APPOnboardingState:
    """APP Onboarding state data model"""
    user_id: str
    current_step: str
    completed_steps: List[str]
    has_started: bool
    is_complete: bool
    last_active_date: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class APPOnboardingService:
    """
    Main service for handling onboarding-related operations for Access Point Providers.
    Manages APP-specific onboarding state persistence, progress tracking, and analytics.
    """

    def __init__(self):
        self.service_name = "APP Onboarding Service"
        self.version = "1.0.0"
        
        # Default onboarding steps for APP users
        self.default_steps = {
            "app": [
                "service_introduction",
                "business_verification",
                "firs_integration_setup", 
                "compliance_settings",
                "taxpayer_setup",
                "invoice_processing_setup",
                "onboarding_complete"
            ]
        }
        
        # Analytics integration
        self.analytics_service = OnboardingAnalyticsService()

        logger.info(f"{self.service_name} v{self.version} initialized")
        
    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle APP onboarding-related operations."""
        try:
            logger.info("Handling APP onboarding operation: %s", operation)

            user_id = payload.get("user_id")
            if not user_id:
                raise ValueError("User ID is required for APP onboarding operations")

            async for session in get_async_session():
                repo = OnboardingStateRepositoryAsync(session)
                return await self._handle_with_repo(repo, operation, payload, user_id)

            raise RuntimeError("Failed to acquire database session for APP onboarding operation")

        except Exception as e:
            logger.error("Error handling APP onboarding operation %s: %s", operation, str(e), exc_info=True)
            raise RuntimeError(f"APP onboarding operation failed: {str(e)}")
    
    async def _handle_get_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get current onboarding state for APP user"""
        try:
            state = await self._get_onboarding_state(repo, user_id)
            return {
                "operation": "get_onboarding_state",
                "success": True,
                "data": self._state_with_progress(state) if state else None,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting APP onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_update_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update APP onboarding state with new progress"""
        try:
            onboarding_data = payload.get("onboarding_data", {})
            
            current_step = onboarding_data.get("current_step")
            completed_steps = onboarding_data.get("completed_steps", [])
            metadata = onboarding_data.get("metadata", {})
            
            if not current_step:
                raise ValueError("Current step is required for state update")
            
            state = await self._update_onboarding_state(
                repo=repo,
                user_id=user_id,
                current_step=current_step,
                completed_steps=completed_steps,
                metadata=metadata,
            )

            return {
                "operation": "update_onboarding_state",
                "success": True,
                "data": self._state_with_progress(state),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error updating APP onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_complete_onboarding_step(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Complete a specific APP onboarding step"""
        try:
            step_name = payload.get("step_name")
            metadata = payload.get("metadata", {})
            
            if not step_name:
                raise ValueError("Step name is required")
            
            state = await self._complete_step(repo, user_id, step_name, metadata)

            return {
                "operation": "complete_onboarding_step",
                "success": True,
                "data": self._state_with_progress(state),
                "step_completed": step_name,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error completing APP onboarding step for user {user_id}: {str(e)}")
            raise

    async def _handle_complete_onboarding(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Mark entire APP onboarding as complete"""
        try:
            completion_metadata = payload.get("completion_metadata", {})
            
            state = await self._complete_onboarding(repo, user_id, completion_metadata)
            
            return {
                "operation": "complete_onboarding",
                "success": True,
                "data": self._state_with_progress(state),
                "user_id": user_id,
                "completed_at": state.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error completing APP onboarding for user {user_id}: {str(e)}")
            raise

    async def _handle_reset_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        """Reset APP onboarding state for user"""
        try:
            await self._reset_onboarding_state(repo, user_id)
            
            return {
                "operation": "reset_onboarding_state",
                "success": True,
                "message": "APP onboarding state reset successfully",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error resetting APP onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_get_onboarding_analytics(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get APP onboarding analytics for user"""
        try:
            analytics = await self._get_onboarding_analytics(repo, user_id)
            
            return {
                "operation": "get_onboarding_analytics",
                "success": True,
                "data": analytics,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting APP onboarding analytics for user {user_id}: {str(e)}")
            raise

    async def _handle_get_business_verification_status(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get business verification status for APP user"""
        try:
            status = await self._get_business_verification_status(repo, user_id)

            return {
                "operation": "get_business_verification_status",
                "success": True,
                "data": status,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting business verification status for user {user_id}: {str(e)}")
            raise

    async def _handle_get_firs_integration_status(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get FIRS integration status for APP user"""
        try:
            status = await self._get_firs_integration_status(repo, user_id)
            
            return {
                "operation": "get_firs_integration_status",
                "success": True,
                "data": status,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting FIRS integration status for user {user_id}: {str(e)}")
            raise

    # Core APP onboarding state management methods

    def _state_with_progress(self, state: APPOnboardingState) -> Dict[str, Any]:
        data = asdict(state)
        data["progress"] = self._calculate_progress(state)
        return data

    def _calculate_progress(self, state: APPOnboardingState) -> Dict[str, Any]:
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

    async def _record_event(
        self,
        *,
        user_id: str,
        step_id: str,
        event_type: str,
        metadata: Dict[str, Any],
    ) -> None:
        try:
            timestamp = self._isoformat(self._utc_now()).replace("+00:00", "Z")
            event = {
                "eventType": event_type,
                "stepId": step_id,
                "userId": user_id,
                "userRole": "access_point_provider",
                "timestamp": timestamp,
                "sessionId": f"app-onboarding-{user_id}",
                "metadata": metadata,
            }
            await self.analytics_service.handle_operation(
                "process_onboarding_events",
                {
                    "events": [event],
                    "batch_timestamp": event["timestamp"],
                },
            )
        except Exception as exc:
            logger.debug("Failed to record onboarding analytics event: %s", exc)

    async def _get_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Optional[APPOnboardingState]:
        """Get APP onboarding state from the database."""
        try:
            record = await self._get_or_create_record(repo, user_id)
            return self._from_orm(record)
        except Exception as e:
            logger.error(f"Error retrieving APP onboarding state for user {user_id}: {str(e)}")
            return None

    async def _get_or_create_record(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> OnboardingStateORM:
        record = await repo.fetch_state(user_id)
        if record is None:
            return await self._create_state_record(repo, user_id, service_package="app")

        if self._ensure_app_metadata(record):
            record = await repo.persist(record)

        return record

    async def _create_state_record(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        *,
        service_package: str = "app",
    ) -> OnboardingStateORM:
        now = self._utc_now()
        metadata = {
            "service_package": service_package,
            "initialization_date": self._isoformat(now),
            "expected_steps": self._expected_steps_for(service_package),
            "business_verification_status": "pending",
            "firs_integration_status": "pending",
        }

        record = OnboardingStateORM(
            user_id=user_id,
            service_package=service_package,
            current_step="service_introduction",
            completed_steps=[],
            has_started=True,
            is_complete=False,
            state_metadata=metadata,
            created_at=now,
            updated_at=now,
            last_active_date=now,
        )

        persisted = await repo.persist(record)
        await self._record_event(
            user_id=user_id,
            step_id="service_introduction",
            event_type="initialize_onboarding",
            metadata={"service_package": service_package},
        )

        logger.info("Initialized new APP onboarding state for user %s", user_id)
        return persisted

    async def _update_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        *,
        current_step: str,
        completed_steps: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> APPOnboardingState:
        record = await self._get_or_create_record(repo, user_id)
        now = self._utc_now()

        existing_steps = list(record.completed_steps or [])
        if completed_steps:
            record.completed_steps = serialize_completed_steps(existing_steps + completed_steps)

        record.current_step = current_step
        record.has_started = True
        record.is_complete = record.is_complete or "onboarding_complete" in record.completed_steps

        metadata_map = dict(record.state_metadata or {})
        if metadata:
            metadata_map.update(metadata)

        metadata_map.setdefault("service_package", "app")
        metadata_map.setdefault("expected_steps", self._expected_steps_for(record.service_package))
        record.state_metadata = metadata_map

        record.last_active_date = now
        record.updated_at = now

        persisted = await repo.persist(record)
        state = self._from_orm(persisted)

        await self._record_event(
            user_id=user_id,
            step_id=current_step,
            event_type="update_state",
            metadata={
                "completed_steps": list(state.completed_steps),
                "metadata": metadata or {},
            },
        )

        return state

    async def _complete_step(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        step_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> APPOnboardingState:
        record = await self._get_or_create_record(repo, user_id)
        now = self._utc_now()

        record.completed_steps = serialize_completed_steps(list(record.completed_steps or []) + [step_name])
        record.current_step = step_name
        record.has_started = True
        record.is_complete = record.is_complete or step_name == "onboarding_complete"

        metadata_map = dict(record.state_metadata or {})
        step_metadata = dict(metadata_map.get("step_metadata", {}))
        step_entry = dict(step_metadata.get(step_name, {}))
        if metadata:
            step_entry.update(metadata)
        step_entry["completed_at"] = self._isoformat(now)
        step_metadata[step_name] = step_entry
        metadata_map["step_metadata"] = step_metadata

        if step_name == "business_verification":
            metadata_map["business_verification_status"] = "completed"
        elif step_name == "firs_integration_setup":
            metadata_map["firs_integration_status"] = "completed"

        metadata_map.setdefault("service_package", "app")
        metadata_map.setdefault("expected_steps", self._expected_steps_for(record.service_package))
        record.state_metadata = metadata_map

        record.last_active_date = now
        record.updated_at = now

        persisted = await repo.persist(record)
        state = self._from_orm(persisted)

        await self._record_event(
            user_id=user_id,
            step_id=step_name,
            event_type="complete_step",
            metadata={
                "step_metadata": metadata or {},
            },
        )

        return state

    async def _complete_onboarding(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
        completion_metadata: Optional[Dict[str, Any]] = None,
    ) -> APPOnboardingState:
        record = await self._get_or_create_record(repo, user_id)
        now = self._utc_now()

        record.completed_steps = serialize_completed_steps(list(record.completed_steps or []) + ["onboarding_complete"])
        record.current_step = "onboarding_complete"
        record.has_started = True
        record.is_complete = True

        metadata_map = dict(record.state_metadata or {})
        step_metadata = dict(metadata_map.get("step_metadata", {}))
        completion_step = dict(step_metadata.get("onboarding_complete", {}))
        if completion_metadata:
            completion_step.update(completion_metadata)
        completion_step["completed_at"] = self._isoformat(now)
        step_metadata["onboarding_complete"] = completion_step
        metadata_map["step_metadata"] = step_metadata

        completion_section = dict(metadata_map.get("completion", {}))
        if completion_metadata:
            completion_section.update(completion_metadata)
        completion_section.setdefault("completed_at", self._isoformat(now))
        completion_section.setdefault("completion_type", "app_onboarding")
        metadata_map["completion"] = completion_section

        if "business_verification" in record.completed_steps:
            metadata_map.setdefault("business_verification_status", "completed")
        if "firs_integration_setup" in record.completed_steps:
            metadata_map.setdefault("firs_integration_status", "completed")

        metadata_map.setdefault("service_package", "app")
        metadata_map.setdefault("expected_steps", self._expected_steps_for(record.service_package))
        record.state_metadata = metadata_map

        record.last_active_date = now
        record.updated_at = now

        persisted = await repo.persist(record)
        state = self._from_orm(persisted)

        await self._record_event(
            user_id=user_id,
            step_id="onboarding_complete",
            event_type="complete_onboarding",
            metadata=completion_metadata or {},
        )

        logger.info("APP onboarding completed for user %s", user_id)
        return state

    async def _reset_onboarding_state(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> None:
        await repo.delete_state(user_id)

        logger.info("APP onboarding state reset for user %s", user_id)
        await self._record_event(
            user_id=user_id,
            step_id="reset",
            event_type="reset_onboarding",
            metadata={},
        )

    async def _get_onboarding_analytics(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        state = await self._get_onboarding_state(repo, user_id)

        if not state:
            return {
                "user_id": user_id,
                "status": "not_started",
                "analytics": {},
            }

        expected_steps = state.metadata.get("expected_steps", [])
        completed_count = len(state.completed_steps)
        total_count = len(expected_steps)
        completion_percentage = (completed_count / total_count * 100) if total_count > 0 else 0

        created_at = self._parse_iso(state.created_at)
        last_active = self._parse_iso(state.last_active_date)
        now = self._utc_now()
        days_since_start = (now - created_at).days
        days_since_last_active = (now - last_active).days

        return {
            "user_id": user_id,
            "status": "complete" if state.is_complete else "in_progress" if state.has_started else "not_started",
            "analytics": {
                "completion_percentage": round(completion_percentage, 1),
                "completed_steps": completed_count,
                "total_steps": total_count,
                "remaining_steps": total_count - completed_count,
                "current_step": state.current_step,
                "days_since_start": days_since_start,
                "days_since_last_active": days_since_last_active,
                "is_stale": days_since_last_active > 7,
                "business_verification_status": state.metadata.get("business_verification_status", "pending"),
                "firs_integration_status": state.metadata.get("firs_integration_status", "pending"),
                "expected_completion": {
                    "next_steps": [step for step in expected_steps if step not in state.completed_steps],
                    "estimated_remaining_time": f"{max(1, total_count - completed_count)} steps remaining",
                },
            },
            "timeline": {
                "started_at": state.created_at,
                "last_active": state.last_active_date,
                "completed_at": state.metadata.get("completion", {}).get("completed_at") if state.is_complete else None,
            },
        }

    async def _get_business_verification_status(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        state = await self._get_onboarding_state(repo, user_id)

        if not state:
            return {
                "status": "not_started",
                "verification_steps": [],
                "required_documents": ["Business registration", "Tax ID", "Bank statements"],
            }

        verification_status = state.metadata.get("business_verification_status", "pending")
        step_metadata = state.metadata.get("step_metadata", {}).get("business_verification", {})

        return {
            "status": verification_status,
            "completed_at": step_metadata.get("completed_at"),
            "verification_steps": [
                {
                    "name": "Business Registration",
                    "status": "completed" if "business_registration" in state.completed_steps else "pending",
                    "required": True,
                },
                {
                    "name": "Tax ID Verification",
                    "status": "completed" if "tax_id_verification" in state.completed_steps else "pending",
                    "required": True,
                },
                {
                    "name": "Bank Account Verification",
                    "status": "completed" if "bank_verification" in state.completed_steps else "pending",
                    "required": True,
                },
            ],
            "metadata": step_metadata,
        }

    async def _get_firs_integration_status(
        self,
        repo: OnboardingStateRepositoryAsync,
        user_id: str,
    ) -> Dict[str, Any]:
        state = await self._get_onboarding_state(repo, user_id)

        if not state:
            return {
                "status": "not_started",
                "integration_steps": [],
                "firs_connection": "not_configured",
            }

        integration_status = state.metadata.get("firs_integration_status", "pending")
        step_metadata = state.metadata.get("step_metadata", {}).get("firs_integration_setup", {})

        return {
            "status": integration_status,
            "completed_at": step_metadata.get("completed_at"),
            "firs_connection": "connected" if "firs_connection" in state.completed_steps else "not_configured",
            "integration_steps": [
                {
                    "name": "FIRS API Configuration",
                    "status": "completed" if "firs_api_config" in state.completed_steps else "pending",
                    "required": True,
                },
                {
                    "name": "Certificate Setup",
                    "status": "completed" if "certificate_setup" in state.completed_steps else "pending",
                    "required": True,
                },
                {
                    "name": "Test Connection",
                    "status": "completed" if "test_connection" in state.completed_steps else "pending",
                    "required": True,
                },
            ],
            "metadata": step_metadata,
        }

    def _from_orm(self, record: OnboardingStateORM) -> APPOnboardingState:
        metadata = dict(record.state_metadata or {})
        metadata.setdefault("service_package", "app")
        metadata.setdefault("expected_steps", self._expected_steps_for(record.service_package))
        metadata.setdefault("business_verification_status", "pending")
        metadata.setdefault("firs_integration_status", "pending")

        return APPOnboardingState(
            user_id=record.user_id,
            current_step=record.current_step,
            completed_steps=list(record.completed_steps or []),
            has_started=record.has_started,
            is_complete=record.is_complete,
            last_active_date=self._isoformat(record.last_active_date),
            metadata=metadata,
            created_at=self._isoformat(record.created_at),
            updated_at=self._isoformat(record.updated_at),
        )

    def _expected_steps_for(self, service_package: Optional[str]) -> List[str]:
        key = service_package or "app"
        return list(self.default_steps.get(key, self.default_steps["app"]))

    def _ensure_app_metadata(self, record: OnboardingStateORM) -> bool:
        changed = False
        metadata = dict(record.state_metadata or {})

        if record.service_package != "app":
            record.service_package = "app"
            changed = True

        if "service_package" not in metadata:
            metadata["service_package"] = "app"
            changed = True

        if "expected_steps" not in metadata or not isinstance(metadata["expected_steps"], list):
            metadata["expected_steps"] = self._expected_steps_for(record.service_package)
            changed = True

        if "business_verification_status" not in metadata:
            metadata["business_verification_status"] = "pending"
            changed = True

        if "firs_integration_status" not in metadata:
            metadata["firs_integration_status"] = "pending"
            changed = True

        if metadata != record.state_metadata:
            record.state_metadata = metadata

        return changed

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _isoformat(value: datetime) -> str:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc).isoformat()
        return str(value)

    @staticmethod
    def _parse_iso(value: str) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)

    async def _handle_with_repo(
        self,
        repo: OnboardingStateRepositoryAsync,
        operation: str,
        payload: Dict[str, Any],
        user_id: str,
    ) -> Dict[str, Any]:
        if operation == "get_onboarding_state":
            return await self._handle_get_onboarding_state(repo, user_id)
        if operation == "update_onboarding_state":
            return await self._handle_update_onboarding_state(repo, user_id, payload)
        if operation == "complete_onboarding_step":
            return await self._handle_complete_onboarding_step(repo, user_id, payload)
        if operation == "complete_onboarding":
            return await self._handle_complete_onboarding(repo, user_id, payload)
        if operation == "reset_onboarding_state":
            return await self._handle_reset_onboarding_state(repo, user_id)
        if operation == "get_onboarding_analytics":
            return await self._handle_get_onboarding_analytics(repo, user_id)
        if operation == "get_business_verification_status":
            return await self._handle_get_business_verification_status(repo, user_id)
        if operation == "get_firs_integration_status":
            return await self._handle_get_firs_integration_status(repo, user_id)

        raise ValueError(f"Unknown APP onboarding operation: {operation}")
