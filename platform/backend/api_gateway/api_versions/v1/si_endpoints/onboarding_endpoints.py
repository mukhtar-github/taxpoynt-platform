"""
Onboarding Management Endpoints - API v1
========================================
System Integrator endpoints for onboarding state management and progress tracking.
Provides centralized onboarding state synchronization across devices and sessions.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import (
    ServiceRole,
    MessageRouter,
    RoutingContext,
    RoutedMessage,
    MessageType,
)

try:
    from core_platform.messaging.redis_message_router import RedisMessageRouter
except Exception:  # pragma: no cover - optional dependency in some envs
    RedisMessageRouter = None
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from core_platform.data_management.db_async import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.idempotency.store import IdempotencyStore
from si_services.onboarding_management.onboarding_service import SIOnboardingService
from core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)

logger = logging.getLogger(__name__)


class OnboardingStateRequest(BaseModel):
    """Request model for updating onboarding state"""
    current_step: str
    completed_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OnboardingStateResponse(BaseModel):
    """Response model for onboarding state"""
    user_id: str
    current_step: str
    completed_steps: List[str]
    has_started: bool
    is_complete: bool
    last_active_date: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class CompanyProfileRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    rc_number: Optional[str] = Field(None, max_length=100)
    tin: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    compliance_contact: Optional[str] = Field(None, max_length=255)
    current_step: Optional[str] = Field(
        default=None,
        description="Optional override for current step; defaults to company-profile.",
    )


class ServiceSelectionRequest(BaseModel):
    selected_package: Optional[str] = Field(
        None, description="Preferred service package for the onboarding journey."
    )
    integration_targets: Optional[List[str]] = Field(
        default=None, description="Identifiers of systems the SI plans to connect."
    )
    primary_use_cases: Optional[List[str]] = Field(
        default=None, description="Key use cases to tailor recommendations."
    )
    go_live_timeline: Optional[str] = Field(
        None, description="Target go-live timeline (e.g., Q1, 30-days)."
    )
    notes: Optional[str] = Field(None, max_length=500)
    current_step: Optional[str] = Field(
        default=None,
        description="Optional override for current step; defaults to service-selection.",
    )


class OnboardingEndpointsV1:
    """
    Onboarding state management endpoints for System Integrators.
    Handles onboarding progress tracking, state synchronization, and resumption.
    """

    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/onboarding",
            tags=["Unified Onboarding Management"],
            dependencies=[Depends(self._require_onboarding_access)]
        )
        
        # Track endpoints for monitoring
        self.endpoint_stats = {
            "total_requests": 0,
            "get_state_requests": 0,
            "update_state_requests": 0,
            "reset_state_requests": 0
        }
        self._local_onboarding_service: Optional[SIOnboardingService] = None
        
        self._setup_routes()

        logger.info("Onboarding Endpoints V1 initialized")

    _CANONICAL_STEP_ORDER: Dict[str, int] = {
        "service-selection": 0,
        "company-profile": 1,
        "system-connectivity": 2,
        "review": 3,
        "launch": 4,
    }
    _LEGACY_TO_CANONICAL: Dict[str, str] = {
        "organization_setup": "service-selection",
        "organization-setup": "service-selection",
        "compliance_verification": "company-profile",
        "compliance-verification": "company-profile",
        "erp_selection": "system-connectivity",
        "erp-selection": "system-connectivity",
        "erp_configuration": "system-connectivity",
        "erp-configuration": "system-connectivity",
        "data_mapping": "system-connectivity",
        "data-mapping": "system-connectivity",
        "testing_validation": "system-connectivity",
        "testing-validation": "system-connectivity",
        "compliance_setup": "review",
        "compliance-setup": "review",
        "production_deployment": "launch",
        "production-deployment": "launch",
        "training_handover": "launch",
        "training-handover": "launch",
    }

    def _router_supports_operation(self, service_role: ServiceRole, operation: str) -> bool:
        """Check if the configured message router advertises an operation for a role."""
        endpoints = getattr(self.message_router, "service_endpoints", None)
        if not isinstance(endpoints, dict):
            return True

        for endpoint in endpoints.values():
            if getattr(endpoint, "service_role", None) != service_role:
                continue
            if not getattr(endpoint, "active", True):
                continue
            metadata = getattr(endpoint, "metadata", {}) or {}
            advertised = metadata.get("operations")
            if not advertised or operation in advertised:
                return True

        return False

    async def _route_onboarding_operation(
        self,
        context: HTTPRoutingContext,
        operation: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Route onboarding operations, compatible with both legacy and updated router signatures."""

        service_role = self._resolve_service_role(context)
        result: Optional[Dict[str, Any]] = None

        if not self._router_supports_operation(service_role, operation):
            logger.info(
                "Message router has no active %s endpoints for onboarding operation '%s'; using direct service path.",
                service_role.value,
                operation,
            )
            return await self._invoke_onboarding_service_direct(operation, payload)

        try:
            result = await self.message_router.route_message(service_role, operation, payload)
        except TypeError as exc:
            message = str(exc)
            if "positional arguments" not in message and "unexpected keyword" not in message:
                raise

            if RedisMessageRouter is not None and isinstance(self.message_router, RedisMessageRouter):
                result = await MessageRouter.route_message(self.message_router, service_role, operation, payload)
            else:
                routing_context = RoutingContext(
                    source_service="api_gateway",
                    source_role=ServiceRole.CORE,
                    target_role=service_role,
                    tenant_id=context.organization_id,
                    routing_metadata={
                        "operation": operation,
                        "api_gateway_route": True,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

                routed_message = RoutedMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.COMMAND,
                    payload=payload,
                    routing_context=routing_context,
                    timestamp=datetime.now(timezone.utc),
                )

                route_msg = getattr(self.message_router, "route_message")
                result = await route_msg(routed_message)
        except Exception as exc:
            logger.warning(
                "Message router dispatch failed for onboarding operation '%s': %s",
                operation,
                exc,
            )

        if result is None:
            try:
                result = await self._invoke_onboarding_service_direct(operation, payload)
            except Exception as direct_error:
                logger.error(
                    "Direct onboarding service invocation failed for '%s': %s",
                    operation,
                    direct_error,
                    exc_info=True,
                )
                return None

        return result

    async def _require_onboarding_access(self, request: Request) -> HTTPRoutingContext:
        """Ensure unified onboarding access for SI, APP, and Hybrid roles."""
        allowed_roles = {
            PlatformRole.SYSTEM_INTEGRATOR,
            PlatformRole.ACCESS_POINT_PROVIDER,
            PlatformRole.HYBRID,
        }

        context = await self.role_detector.detect_role_context(request)
        if not context or context.primary_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Onboarding access requires SI, APP, or Hybrid role",
            )

        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for onboarding endpoint",
            )

        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "onboarding"
        context.metadata.setdefault("service_package", self._infer_service_package(context))

        if not context.user_id:
            header_user = request.headers.get("x-user-id") or request.headers.get("X-User-Id")
            if header_user:
                context.user_id = header_user
        if not context.organization_id:
            header_org = request.headers.get("x-organization-id") or request.headers.get("X-Organization-Id")
            if header_org:
                context.organization_id = header_org
        header_user_log = request.headers.get("x-user-id") or request.headers.get("X-User-Id")
        if header_user_log:
            logger.info("Onboarding request header user id: %s", header_user_log)
        if context.user_id:
            context.metadata.setdefault("user_id", context.user_id)
            logger.info("Resolved onboarding user id: %s", context.user_id)
        
        return context

    @staticmethod
    def _infer_service_package(context: HTTPRoutingContext) -> str:
        role = context.primary_role
        if role == PlatformRole.ACCESS_POINT_PROVIDER:
            return "app"
        if role == PlatformRole.HYBRID:
            return "hybrid"
        return "si"

    @staticmethod
    def _resolve_service_role(context: HTTPRoutingContext) -> ServiceRole:
        role = context.primary_role
        if role == PlatformRole.ACCESS_POINT_PROVIDER:
            return ServiceRole.ACCESS_POINT_PROVIDER
        if role == PlatformRole.HYBRID:
            # Hybrid onboarding currently funnels through the unified service registered under SI
            return ServiceRole.SYSTEM_INTEGRATOR
        return ServiceRole.SYSTEM_INTEGRATOR

    def _setup_routes(self):
        """Setup onboarding state management routes"""
        
        # Get current onboarding state
        self.router.add_api_route(
            "/state",
            self.get_onboarding_state,
            methods=["GET"],
            summary="Get current onboarding state",
            description="Retrieve the current onboarding progress and state for the authenticated user",
            response_model=V1ResponseModel
        )
        
        # Update onboarding state
        self.router.add_api_route(
            "/state",
            self.update_onboarding_state,
            methods=["PUT"],
            summary="Update onboarding state",
            description="Update the current onboarding step and progress",
            response_model=V1ResponseModel
        )
        
        # Complete specific onboarding step
        self.router.add_api_route(
            "/state/step/{step_name}/complete",
            self.complete_onboarding_step,
            methods=["POST"],
            summary="Mark onboarding step as complete",
            description="Mark a specific onboarding step as completed",
            response_model=V1ResponseModel
        )
        
        # Mark entire onboarding as complete
        self.router.add_api_route(
            "/complete",
            self.complete_onboarding,
            methods=["POST"],
            summary="Complete onboarding",
            description="Mark the entire onboarding process as complete",
            response_model=V1ResponseModel
        )
        
        # Reset onboarding state (for testing/re-onboarding)
        self.router.add_api_route(
            "/state/reset",
            self.reset_onboarding_state,
            methods=["DELETE"],
            summary="Reset onboarding state",
            description="Reset onboarding state to start over (admin/testing only)",
            response_model=V1ResponseModel
        )
        
        # Get onboarding analytics for user
        self.router.add_api_route(
            "/analytics",
            self.get_onboarding_analytics,
            methods=["GET"],
            summary="Get onboarding analytics",
            description="Get detailed analytics about onboarding progress and completion",
            response_model=V1ResponseModel
        )

        # Wizard autosave endpoints
        self.router.add_api_route(
            "/wizard/company-profile",
            self.save_company_profile,
            methods=["PUT"],
            summary="Save company profile details",
            description="Autosave company profile information for the onboarding wizard",
            response_model=V1ResponseModel,
        )
        self.router.add_api_route(
            "/wizard/service-selection",
            self.save_service_selection,
            methods=["PUT"],
            summary="Save service selection details",
            description="Autosave service selection preferences for the onboarding wizard",
            response_model=V1ResponseModel,
        )

    # Core Onboarding State Management
    async def get_onboarding_state(self, request: Request):
        """Get current onboarding state for the authenticated user"""
        try:
            context = await self._require_onboarding_access(request)
            self.endpoint_stats["get_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            mock_state = self._build_fallback_state(context)

            result = await self._route_onboarding_operation(
                context,
                "get_onboarding_state",
                {
                    "user_id": context.user_id,
                    "service_package": context.metadata.get("service_package"),
                    "api_version": "v1",
                },
            )

            # Fall back to mock result if downstream services are unavailable
            if not result or not isinstance(result, dict) or not result.get("success"):
                fallback_payload = {"success": True, "data": mock_state, "fallback": True}
                return self._create_v1_response(fallback_payload, "onboarding_state_retrieved")

            return self._create_v1_response(result, "onboarding_state_retrieved")
        except RuntimeError as service_error:
            logger.warning(
                "Onboarding state service unavailable, returning mock state: %s",
                service_error,
            )
            fallback_payload = {
                "success": True,
                "data": mock_state,
                "fallback": True,
                "error_message": str(service_error),
            }
            return self._create_v1_response(fallback_payload, "onboarding_state_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting onboarding state in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get onboarding state")

    async def update_onboarding_state(self,
                                      request: Request,
                                      db: AsyncSession = Depends(get_async_session)):
        """Update onboarding state with new progress"""
        try:
            self.endpoint_stats["update_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            context = await self._require_onboarding_access(request)
            body = await request.json()
            
            # Validate required fields
            required_fields = ["current_step"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Idempotency
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(body)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "onboarding_state_updated", status_code=stored_code or 200)

            result = await self._route_onboarding_operation(
                context,
                "update_onboarding_state",
                {
                    "user_id": context.user_id,
                    "onboarding_data": body,
                    "service_package": context.metadata.get("service_package"),
                    "api_version": "v1"
                }
            )
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return self._create_v1_response(result, "onboarding_state_updated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating onboarding state in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to update onboarding state")

    async def complete_onboarding_step(self,
                                       step_name: str,
                                       request: Request,
                                       db: AsyncSession = Depends(get_async_session)):
        """Mark a specific onboarding step as complete"""
        try:
            context = await self._require_onboarding_access(request)
            body = await request.json() if hasattr(request, 'json') else {}
            
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                composite = {"step_name": step_name, "metadata": body.get("metadata", {})}
                req_hash = IdempotencyStore.compute_request_hash(composite)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "onboarding_step_completed", status_code=stored_code or 200)

            result = await self._route_onboarding_operation(
                context,
                "complete_onboarding_step",
                {
                    "user_id": context.user_id,
                    "step_name": step_name,
                    "metadata": body.get("metadata", {}),
                    "service_package": context.metadata.get("service_package"),
                    "api_version": "v1"
                }
            )
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return self._create_v1_response(result, "onboarding_step_completed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing onboarding step in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to complete onboarding step")

    async def complete_onboarding(self,
                                  request: Request,
                                  db: AsyncSession = Depends(get_async_session)):
        """Mark entire onboarding as complete"""
        try:
            context = await self._require_onboarding_access(request)
            body = await request.json() if hasattr(request, 'json') else {}
            
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(body)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "onboarding_completed", status_code=stored_code or 200)

            result = await self._route_onboarding_operation(
                context,
                "complete_onboarding",
                {
                    "user_id": context.user_id,
                    "completion_metadata": body.get("metadata", {}),
                    "service_package": context.metadata.get("service_package"),
                    "api_version": "v1"
                }
            )
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return self._create_v1_response(result, "onboarding_completed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing onboarding in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to complete onboarding")

    async def reset_onboarding_state(self, request: Request, db: AsyncSession = Depends(get_async_session)):
        """Reset onboarding state (admin/testing only)"""
        try:
            context = await self._require_onboarding_access(request)
            self.endpoint_stats["reset_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            # Optional idempotency for destructive reset
            # A reset with the same key will be a no-op replay
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash({"action": "reset_onboarding_state"})
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    method="DELETE",
                    endpoint="/onboarding/state/reset",
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "onboarding_state_reset", status_code=stored_code or 200)

            result = await self._route_onboarding_operation(
                context,
                "reset_onboarding_state",
                {
                    "user_id": context.user_id,
                    "service_package": context.metadata.get("service_package"),
                    "api_version": "v1"
                }
            )
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return self._create_v1_response(result, "onboarding_state_reset")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting onboarding state in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to reset onboarding state")

    async def get_onboarding_analytics(self, request: Request):
        """Get onboarding analytics and progress insights"""
        try:
            context = await self._require_onboarding_access(request)
            result = await self._route_onboarding_operation(
                context,
                "get_onboarding_analytics",
                {
                    "user_id": context.user_id,
                    "service_package": context.metadata.get("service_package"),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_analytics_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting onboarding analytics in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get onboarding analytics")

    def _create_v1_response(self, data: Any, message: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized V1 response"""
        return build_v1_response(data, action=message)

    def _build_fallback_state(self, context: HTTPRoutingContext) -> Dict[str, Any]:
        """Construct a minimal onboarding state when downstream services are unavailable."""
        now_iso = datetime.now(timezone.utc).isoformat()
        service_package = context.metadata.get("service_package") or self._infer_service_package(context)

        onboarding_service = SIOnboardingService()
        expected_steps = onboarding_service.PACKAGE_FLOWS.get(
            service_package,
            onboarding_service.PACKAGE_FLOWS["si"],
        )
        step_definitions = {
            step: onboarding_service.STEP_DEFINITIONS.get(
                step, {"title": step, "description": "", "success_criteria": ""}
            )
            for step in expected_steps
        }

        return {
            "user_id": context.user_id or "",
            "current_step": expected_steps[0] if expected_steps else "service-selection",
            "completed_steps": [],
            "has_started": False,
            "is_complete": False,
            "last_active_date": now_iso,
            "metadata": {
                "service_package": service_package,
                "expected_steps": expected_steps,
                "step_definitions": step_definitions,
                "fallback": True,
                "fallback_reason": "onboarding_service_unavailable",
            },
            "created_at": now_iso,
            "updated_at": now_iso,
        }

    async def _invoke_onboarding_service_direct(
        self,
        operation: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Invoke SI onboarding service directly when message router is unavailable."""
        if self._local_onboarding_service is None:
            self._local_onboarding_service = SIOnboardingService()
        return await self._local_onboarding_service.handle_operation(operation, payload)

    @staticmethod
    def _strip_none(data: Dict[str, Any]) -> Dict[str, Any]:
        return {key: value for key, value in data.items() if value is not None}

    def _canonicalize_step(self, step: Optional[str]) -> str:
        if not step:
            return "service-selection"
        normalized = step.strip().lower().replace(" ", "-")
        normalized = normalized.replace("_", "-")
        return self._LEGACY_TO_CANONICAL.get(normalized, normalized)

    def _max_canonical_step(self, existing: str, candidate: str) -> str:
        existing_rank = self._CANONICAL_STEP_ORDER.get(existing, -1)
        candidate_rank = self._CANONICAL_STEP_ORDER.get(candidate, -1)
        return existing if existing_rank >= candidate_rank else candidate

    def _invalidate_local_service_cache(self, user_id: Optional[str]) -> None:
        """Invalidate cached onboarding state when repositories are written to directly."""
        if not user_id:
            return
        if self._local_onboarding_service is None:
            try:
                self._local_onboarding_service = SIOnboardingService()
            except Exception:
                return
        try:
            self._local_onboarding_service._invalidate_cache(user_id)  # type: ignore[attr-defined]
        except AttributeError:
            pass

    async def save_company_profile(
        self,
        payload: CompanyProfileRequest,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ):
        """Autosave company profile details within the onboarding wizard."""
        try:
            context = await self._require_onboarding_access(request)
            service_package = context.metadata.get("service_package") or self._infer_service_package(context)
            if not context.user_id:
                raise HTTPException(status_code=400, detail="User context required for company profile save")
            user_id = str(context.user_id)

            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(payload.dict())
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=user_id,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "company_profile_saved", status_code=stored_code or 200)

            repo = OnboardingStateRepositoryAsync(db)
            current_state = await repo.ensure_state(user_id, service_package)
            existing_step = self._canonicalize_step(current_state.current_step)
            requested_step = self._canonicalize_step(payload.current_step or "company-profile")
            target_step = self._max_canonical_step(existing_step, requested_step)

            profile_payload = self._strip_none(
                payload.dict(exclude={"current_step"}, exclude_unset=True)
            )

            await repo.upsert_wizard_section(
                user_id,
                service_package,
                section="company_profile",
                payload=profile_payload,
                current_step=target_step,
            )

            self._invalidate_local_service_cache(user_id)

            result = await self._invoke_onboarding_service_direct(
                "get_onboarding_state",
                {
                    "user_id": user_id,
                    "service_package": service_package,
                    "api_version": "v1",
                },
            )

            response = self._create_v1_response(result, "company_profile_saved")
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=user_id,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return response
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("Error saving company profile: %s", exc, exc_info=True)
            raise HTTPException(status_code=502, detail="Failed to save company profile")

    async def save_service_selection(
        self,
        payload: ServiceSelectionRequest,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ):
        """Autosave service selection preferences within the onboarding wizard."""
        try:
            context = await self._require_onboarding_access(request)
            service_package = context.metadata.get("service_package") or self._infer_service_package(context)
            if not context.user_id:
                raise HTTPException(status_code=400, detail="User context required for service selection save")
            user_id = str(context.user_id)

            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(payload.dict())
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=user_id,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "service_selection_saved", status_code=stored_code or 200)

            repo = OnboardingStateRepositoryAsync(db)
            current_state = await repo.ensure_state(user_id, service_package)
            existing_step = self._canonicalize_step(current_state.current_step)
            requested_step = self._canonicalize_step(payload.current_step or "service-selection")
            target_step = self._max_canonical_step(existing_step, requested_step)

            selection_payload = self._strip_none(
                payload.dict(exclude={"current_step"}, exclude_unset=True)
            )

            await repo.upsert_wizard_section(
                user_id,
                service_package,
                section="service_focus",
                payload=selection_payload,
                current_step=target_step,
            )

            self._invalidate_local_service_cache(user_id)

            result = await self._invoke_onboarding_service_direct(
                "get_onboarding_state",
                {
                    "user_id": user_id,
                    "service_package": service_package,
                    "api_version": "v1",
                },
            )

            response = self._create_v1_response(result, "service_selection_saved")
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=user_id,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return response
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("Error saving service selection: %s", exc, exc_info=True)
            raise HTTPException(status_code=502, detail="Failed to save service selection")


def create_onboarding_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create onboarding management router"""
    endpoints = OnboardingEndpointsV1(role_detector, permission_guard, message_router)
    return endpoints.router
