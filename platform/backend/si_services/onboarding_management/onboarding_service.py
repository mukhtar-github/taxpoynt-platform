"""
SI Onboarding Service
====================

Service for handling onboarding state management operations for System Integrators.
Provides centralized onboarding progress tracking, state synchronization, and analytics.

Operations Handled:
- get_onboarding_state
- update_onboarding_state  
- complete_onboarding_step
- complete_onboarding
- reset_onboarding_state
- get_onboarding_analytics

Architecture:
- Follows SI service patterns
- Handles message router operations
- Provides database persistence for onboarding state
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class OnboardingState:
    """Onboarding state data model"""
    user_id: str
    current_step: str
    completed_steps: List[str]
    has_started: bool
    is_complete: bool
    last_active_date: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class SIOnboardingService:
    """
    Main service for handling onboarding-related operations for System Integrators.
    Manages onboarding state persistence, progress tracking, and analytics.
    """

    def __init__(self):
        self.service_name = "SI Onboarding Service"
        self.version = "1.0.0"
        
        # Default onboarding steps for different service packages
        self.default_steps = {
            "si": [
                "service_introduction",
                "integration_choice", 
                "business_systems_setup",
                "financial_systems_setup",
                "banking_connected",
                "reconciliation_setup",
                "complete_integration_setup",
                "onboarding_complete"
            ],
            "app": [
                "service_introduction",
                "business_verification",
                "firs_integration_setup", 
                "compliance_settings",
                "onboarding_complete"
            ],
            "hybrid": [
                "service_introduction",
                "service_selection",
                "combined_setup",
                "onboarding_complete"
            ]
        }
        
        # In-memory storage for now (replace with database in production)
        self._onboarding_states: Dict[str, OnboardingState] = {}
        
        logger.info(f"{self.service_name} v{self.version} initialized")
        
    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle onboarding-related operations.
        
        Args:
            operation: Operation name
            payload: Operation payload containing user_id and operation-specific data
            
        Returns:
            Dict with operation results
        """
        try:
            logger.info(f"Handling onboarding operation: {operation}")
            
            # Extract common payload data
            user_id = payload.get("user_id")
            api_version = payload.get("api_version", "v1")
            
            if not user_id:
                raise ValueError("User ID is required for onboarding operations")
            
            # Route to appropriate handler
            if operation == "get_onboarding_state":
                return await self._handle_get_onboarding_state(user_id, payload)
            elif operation == "update_onboarding_state":
                return await self._handle_update_onboarding_state(user_id, payload)
            elif operation == "complete_onboarding_step":
                return await self._handle_complete_onboarding_step(user_id, payload)
            elif operation == "complete_onboarding":
                return await self._handle_complete_onboarding(user_id, payload)
            elif operation == "reset_onboarding_state":
                return await self._handle_reset_onboarding_state(user_id, payload)
            elif operation == "get_onboarding_analytics":
                return await self._handle_get_onboarding_analytics(user_id, payload)
            elif operation == "initiate_organization_onboarding":
                org_id = payload.get("org_id")
                return {"operation": operation, "success": True, "organization_id": org_id, "initiated": True}
            elif operation == "get_organization_onboarding_status":
                org_id = payload.get("org_id")
                return {"operation": operation, "success": True, "organization_id": org_id, "status": "pending"}
            else:
                raise ValueError(f"Unknown onboarding operation: {operation}")
                
        except Exception as e:
            logger.error(f"Error handling onboarding operation {operation}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Onboarding operation failed: {str(e)}")
    
    async def _handle_get_onboarding_state(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get current onboarding state for user"""
        try:
            state = await self._get_onboarding_state(user_id)
            
            return {
                "operation": "get_onboarding_state",
                "success": True,
                "data": asdict(state) if state else None,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_update_onboarding_state(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update onboarding state with new progress"""
        try:
            onboarding_data = payload.get("onboarding_data", {})
            
            current_step = onboarding_data.get("current_step")
            completed_steps = onboarding_data.get("completed_steps", [])
            metadata = onboarding_data.get("metadata", {})
            
            if not current_step:
                raise ValueError("Current step is required for state update")
            
            state = await self._update_onboarding_state(
                user_id=user_id,
                current_step=current_step,
                completed_steps=completed_steps,
                metadata=metadata
            )
            
            return {
                "operation": "update_onboarding_state",
                "success": True,
                "data": asdict(state),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error updating onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_complete_onboarding_step(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a specific onboarding step"""
        try:
            step_name = payload.get("step_name")
            metadata = payload.get("metadata", {})
            
            if not step_name:
                raise ValueError("Step name is required")
            
            state = await self._complete_step(user_id, step_name, metadata)
            
            return {
                "operation": "complete_onboarding_step",
                "success": True,
                "data": asdict(state),
                "step_completed": step_name,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error completing onboarding step for user {user_id}: {str(e)}")
            raise

    async def _handle_complete_onboarding(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mark entire onboarding as complete"""
        try:
            completion_metadata = payload.get("completion_metadata", {})
            
            state = await self._complete_onboarding(user_id, completion_metadata)
            
            return {
                "operation": "complete_onboarding",
                "success": True,
                "data": asdict(state),
                "user_id": user_id,
                "completed_at": state.updated_at
            }
            
        except Exception as e:
            logger.error(f"Error completing onboarding for user {user_id}: {str(e)}")
            raise

    async def _handle_reset_onboarding_state(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Reset onboarding state for user"""
        try:
            await self._reset_onboarding_state(user_id)
            
            return {
                "operation": "reset_onboarding_state",
                "success": True,
                "message": "Onboarding state reset successfully",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error resetting onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_get_onboarding_analytics(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get onboarding analytics for user"""
        try:
            analytics = await self._get_onboarding_analytics(user_id)
            
            return {
                "operation": "get_onboarding_analytics",
                "success": True,
                "data": analytics,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting onboarding analytics for user {user_id}: {str(e)}")
            raise

    # Core onboarding state management methods
    async def _get_onboarding_state(self, user_id: str) -> Optional[OnboardingState]:
        """Get onboarding state from storage"""
        try:
            # For now, use in-memory storage (replace with database query)
            state = self._onboarding_states.get(user_id)
            
            if not state:
                # Initialize new onboarding state if none exists
                state = await self._initialize_onboarding_state(user_id)
            
            return state
            
        except Exception as e:
            logger.error(f"Error retrieving onboarding state for user {user_id}: {str(e)}")
            return None

    async def _initialize_onboarding_state(self, user_id: str, service_package: str = "si") -> OnboardingState:
        """Initialize new onboarding state for user"""
        now = datetime.utcnow().isoformat()
        
        state = OnboardingState(
            user_id=user_id,
            current_step="service_introduction",
            completed_steps=[],
            has_started=True,
            is_complete=False,
            last_active_date=now,
            metadata={
                "service_package": service_package,
                "initialization_date": now,
                "expected_steps": self.default_steps.get(service_package, self.default_steps["si"])
            },
            created_at=now,
            updated_at=now
        )
        
        # Store in memory (replace with database insert)
        self._onboarding_states[user_id] = state
        
        logger.info(f"Initialized new onboarding state for user {user_id}")
        return state

    async def _update_onboarding_state(self, 
                                      user_id: str, 
                                      current_step: str,
                                      completed_steps: List[str] = None,
                                      metadata: Dict[str, Any] = None) -> OnboardingState:
        """Update onboarding state"""
        state = await self._get_onboarding_state(user_id)
        if not state:
            state = await self._initialize_onboarding_state(user_id)
        
        # Update state
        state.current_step = current_step
        if completed_steps is not None:
            state.completed_steps = list(set(state.completed_steps + completed_steps))
        if metadata:
            state.metadata.update(metadata)
        
        state.last_active_date = datetime.utcnow().isoformat()
        state.updated_at = datetime.utcnow().isoformat()
        
        # Check if onboarding is complete
        if "onboarding_complete" in state.completed_steps:
            state.is_complete = True
        
        # Store updated state (replace with database update)
        self._onboarding_states[user_id] = state
        
        return state

    async def _complete_step(self, user_id: str, step_name: str, metadata: Dict[str, Any] = None) -> OnboardingState:
        """Mark a specific step as complete"""
        state = await self._get_onboarding_state(user_id)
        if not state:
            state = await self._initialize_onboarding_state(user_id)
        
        # Add step to completed steps if not already there
        if step_name not in state.completed_steps:
            state.completed_steps.append(step_name)
        
        # Update metadata
        if metadata:
            step_metadata = state.metadata.get("step_metadata", {})
            step_metadata[step_name] = {
                **metadata,
                "completed_at": datetime.utcnow().isoformat()
            }
            state.metadata["step_metadata"] = step_metadata
        
        state.last_active_date = datetime.utcnow().isoformat()
        state.updated_at = datetime.utcnow().isoformat()
        
        # Store updated state
        self._onboarding_states[user_id] = state
        
        return state

    async def _complete_onboarding(self, user_id: str, completion_metadata: Dict[str, Any] = None) -> OnboardingState:
        """Mark entire onboarding as complete"""
        state = await self._complete_step(user_id, "onboarding_complete", completion_metadata)
        state.is_complete = True
        state.current_step = "onboarding_complete"
        
        # Add completion metadata
        state.metadata["completion"] = {
            **(completion_metadata or {}),
            "completed_at": datetime.utcnow().isoformat()
        }
        
        # Store updated state
        self._onboarding_states[user_id] = state
        
        logger.info(f"Onboarding completed for user {user_id}")
        return state

    async def _reset_onboarding_state(self, user_id: str) -> None:
        """Reset onboarding state for user"""
        if user_id in self._onboarding_states:
            del self._onboarding_states[user_id]
        
        logger.info(f"Onboarding state reset for user {user_id}")

    async def _get_onboarding_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get onboarding analytics and insights"""
        state = await self._get_onboarding_state(user_id)
        
        if not state:
            return {
                "user_id": user_id,
                "status": "not_started",
                "analytics": {}
            }
        
        # Calculate analytics
        expected_steps = state.metadata.get("expected_steps", [])
        completed_count = len(state.completed_steps)
        total_count = len(expected_steps)
        completion_percentage = (completed_count / total_count * 100) if total_count > 0 else 0
        
        # Calculate time metrics
        created_at = datetime.fromisoformat(state.created_at.replace('Z', '+00:00') if state.created_at.endswith('Z') else state.created_at)
        last_active = datetime.fromisoformat(state.last_active_date.replace('Z', '+00:00') if state.last_active_date.endswith('Z') else state.last_active_date)
        days_since_start = (datetime.utcnow().replace(tzinfo=created_at.tzinfo) - created_at).days
        days_since_last_active = (datetime.utcnow().replace(tzinfo=last_active.tzinfo) - last_active).days
        
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
                "is_stale": days_since_last_active > 7,  # Consider stale if inactive for 7+ days
                "expected_completion": {
                    "next_steps": [step for step in expected_steps if step not in state.completed_steps],
                    "estimated_remaining_time": f"{max(1, total_count - completed_count)} steps remaining"
                }
            },
            "timeline": {
                "started_at": state.created_at,
                "last_active": state.last_active_date,
                "completed_at": state.metadata.get("completion", {}).get("completed_at") if state.is_complete else None
            }
        }
