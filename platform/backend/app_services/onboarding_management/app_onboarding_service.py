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
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

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
        
        # In-memory storage for now (replace with database in production)
        self._onboarding_states: Dict[str, APPOnboardingState] = {}
        
        logger.info(f"{self.service_name} v{self.version} initialized")
        
    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle APP onboarding-related operations.
        
        Args:
            operation: Operation name
            payload: Operation payload containing user_id and operation-specific data
            
        Returns:
            Dict with operation results
        """
        try:
            logger.info(f"Handling APP onboarding operation: {operation}")
            
            # Extract common payload data
            user_id = payload.get("user_id")
            api_version = payload.get("api_version", "v1")
            
            if not user_id:
                raise ValueError("User ID is required for APP onboarding operations")
            
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
            elif operation == "get_business_verification_status":
                return await self._handle_get_business_verification_status(user_id, payload)
            elif operation == "get_firs_integration_status":
                return await self._handle_get_firs_integration_status(user_id, payload)
            else:
                raise ValueError(f"Unknown APP onboarding operation: {operation}")
                
        except Exception as e:
            logger.error(f"Error handling APP onboarding operation {operation}: {str(e)}", exc_info=True)
            raise RuntimeError(f"APP onboarding operation failed: {str(e)}")
    
    async def _handle_get_onboarding_state(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get current onboarding state for APP user"""
        try:
            state = await self._get_onboarding_state(user_id)
            
            return {
                "operation": "get_onboarding_state",
                "success": True,
                "data": asdict(state) if state else None,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting APP onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_update_onboarding_state(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update APP onboarding state with new progress"""
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
            logger.error(f"Error updating APP onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_complete_onboarding_step(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a specific APP onboarding step"""
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
            logger.error(f"Error completing APP onboarding step for user {user_id}: {str(e)}")
            raise

    async def _handle_complete_onboarding(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mark entire APP onboarding as complete"""
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
            logger.error(f"Error completing APP onboarding for user {user_id}: {str(e)}")
            raise

    async def _handle_reset_onboarding_state(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Reset APP onboarding state for user"""
        try:
            await self._reset_onboarding_state(user_id)
            
            return {
                "operation": "reset_onboarding_state",
                "success": True,
                "message": "APP onboarding state reset successfully",
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error resetting APP onboarding state for user {user_id}: {str(e)}")
            raise

    async def _handle_get_onboarding_analytics(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get APP onboarding analytics for user"""
        try:
            analytics = await self._get_onboarding_analytics(user_id)
            
            return {
                "operation": "get_onboarding_analytics",
                "success": True,
                "data": analytics,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting APP onboarding analytics for user {user_id}: {str(e)}")
            raise

    async def _handle_get_business_verification_status(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get business verification status for APP user"""
        try:
            status = await self._get_business_verification_status(user_id)
            
            return {
                "operation": "get_business_verification_status",
                "success": True,
                "data": status,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting business verification status for user {user_id}: {str(e)}")
            raise

    async def _handle_get_firs_integration_status(self, user_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get FIRS integration status for APP user"""
        try:
            status = await self._get_firs_integration_status(user_id)
            
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
    async def _get_onboarding_state(self, user_id: str) -> Optional[APPOnboardingState]:
        """Get APP onboarding state from storage"""
        try:
            # For now, use in-memory storage (replace with database query)
            state = self._onboarding_states.get(user_id)
            
            if not state:
                # Initialize new APP onboarding state if none exists
                state = await self._initialize_onboarding_state(user_id)
            
            return state
            
        except Exception as e:
            logger.error(f"Error retrieving APP onboarding state for user {user_id}: {str(e)}")
            return None

    async def _initialize_onboarding_state(self, user_id: str, service_package: str = "app") -> APPOnboardingState:
        """Initialize new APP onboarding state for user"""
        now = datetime.utcnow().isoformat()
        
        state = APPOnboardingState(
            user_id=user_id,
            current_step="service_introduction",
            completed_steps=[],
            has_started=True,
            is_complete=False,
            last_active_date=now,
            metadata={
                "service_package": service_package,
                "initialization_date": now,
                "expected_steps": self.default_steps.get(service_package, self.default_steps["app"]),
                "business_verification_status": "pending",
                "firs_integration_status": "pending"
            },
            created_at=now,
            updated_at=now
        )
        
        # Store in memory (replace with database insert)
        self._onboarding_states[user_id] = state
        
        logger.info(f"Initialized new APP onboarding state for user {user_id}")
        return state

    async def _update_onboarding_state(self, 
                                      user_id: str, 
                                      current_step: str,
                                      completed_steps: List[str] = None,
                                      metadata: Dict[str, Any] = None) -> APPOnboardingState:
        """Update APP onboarding state"""
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

    async def _complete_step(self, user_id: str, step_name: str, metadata: Dict[str, Any] = None) -> APPOnboardingState:
        """Mark a specific APP step as complete"""
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
        
        # Update specific APP step statuses
        if step_name == "business_verification":
            state.metadata["business_verification_status"] = "completed"
        elif step_name == "firs_integration_setup":
            state.metadata["firs_integration_status"] = "completed"
        
        state.last_active_date = datetime.utcnow().isoformat()
        state.updated_at = datetime.utcnow().isoformat()
        
        # Store updated state
        self._onboarding_states[user_id] = state
        
        return state

    async def _complete_onboarding(self, user_id: str, completion_metadata: Dict[str, Any] = None) -> APPOnboardingState:
        """Mark entire APP onboarding as complete"""
        state = await self._complete_step(user_id, "onboarding_complete", completion_metadata)
        state.is_complete = True
        state.current_step = "onboarding_complete"
        
        # Add completion metadata
        state.metadata["completion"] = {
            **(completion_metadata or {}),
            "completed_at": datetime.utcnow().isoformat(),
            "completion_type": "app_onboarding"
        }
        
        # Store updated state
        self._onboarding_states[user_id] = state
        
        logger.info(f"APP onboarding completed for user {user_id}")
        return state

    async def _reset_onboarding_state(self, user_id: str) -> None:
        """Reset APP onboarding state for user"""
        if user_id in self._onboarding_states:
            del self._onboarding_states[user_id]
        
        logger.info(f"APP onboarding state reset for user {user_id}")

    async def _get_onboarding_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get APP onboarding analytics and insights"""
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
                "business_verification_status": state.metadata.get("business_verification_status", "pending"),
                "firs_integration_status": state.metadata.get("firs_integration_status", "pending"),
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

    async def _get_business_verification_status(self, user_id: str) -> Dict[str, Any]:
        """Get business verification status for APP user"""
        state = await self._get_onboarding_state(user_id)
        
        if not state:
            return {
                "status": "not_started",
                "verification_steps": [],
                "required_documents": ["Business registration", "Tax ID", "Bank statements"]
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
                    "required": True
                },
                {
                    "name": "Tax ID Verification",
                    "status": "completed" if "tax_id_verification" in state.completed_steps else "pending",
                    "required": True
                },
                {
                    "name": "Bank Account Verification",
                    "status": "completed" if "bank_verification" in state.completed_steps else "pending",
                    "required": True
                }
            ],
            "metadata": step_metadata
        }

    async def _get_firs_integration_status(self, user_id: str) -> Dict[str, Any]:
        """Get FIRS integration status for APP user"""
        state = await self._get_onboarding_state(user_id)
        
        if not state:
            return {
                "status": "not_started",
                "integration_steps": [],
                "firs_connection": "not_configured"
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
                    "required": True
                },
                {
                    "name": "Certificate Setup",
                    "status": "completed" if "certificate_setup" in state.completed_steps else "pending",
                    "required": True
                },
                {
                    "name": "Test Connection",
                    "status": "completed" if "test_connection" in state.completed_steps else "pending",
                    "required": True
                }
            ],
            "metadata": step_metadata
        }
