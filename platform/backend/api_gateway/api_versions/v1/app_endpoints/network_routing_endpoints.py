"""
Network Routing Endpoints - API v1 (APP)
========================================
Minimal four-corner participant registry and resolver for delivery routing.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response

logger = logging.getLogger(__name__)


class NetworkRoutingEndpointsV1:
    def __init__(self, role_detector: HTTPRoleDetector, permission_guard: APIPermissionGuard, message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/network", tags=["Network Routing V1"], dependencies=[Depends(self._require_app_role)])
        self._setup_routes()

    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        context = await self.role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Point Provider role required for v1 API")
        if not await self.permission_guard.check_endpoint_permission(context, f"v1/app{request.url.path}", request.method):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for APP v1 endpoint")
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "app"
        return context

    def _setup_routes(self):
        # Participant registry CRUD
        self.router.add_api_route("/participants", self.list_participants, methods=["GET"], summary="List participants", response_model=V1ResponseModel)
        self.router.add_api_route("/participants", self.register_participant, methods=["POST"], summary="Register participant", response_model=V1ResponseModel, status_code=201)
        self.router.add_api_route("/participants/{identifier}", self.get_participant, methods=["GET"], summary="Get participant", response_model=V1ResponseModel)
        self.router.add_api_route("/participants/{participant_id}", self.update_participant, methods=["PUT"], summary="Update participant", response_model=V1ResponseModel)
        # Optional: direct UUID lookup to avoid path ambiguity with identifier
        self.router.add_api_route("/participants/id/{participant_id}", self.get_participant_by_id, methods=["GET"], summary="Get participant by UUID", response_model=V1ResponseModel)
        # Resolver
        self.router.add_api_route("/resolve", self.resolve_participant, methods=["POST"], summary="Resolve participant by identifier", response_model=V1ResponseModel)

    async def list_participants(self, request: Request, limit: int = Query(50, ge=1, le=1000), page: int = Query(1, ge=1), status: Optional[str] = Query(None), role: Optional[str] = Query(None), org_id: Optional[str] = Query(None)):
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_participants",
                payload={
                    "limit": limit,
                    "page": page,
                    "status": status,
                    "role": role,
                    "organization_id": org_id,
                    "api_version": "v1",
                },
            )
            return build_v1_response(result, "participants_listed")
        except Exception as e:
            logger.error(f"Error listing participants: {e}")
            raise HTTPException(status_code=500, detail="Failed to list participants")

    async def register_participant(self, request: Request):
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            required = ["identifier", "role", "ap_endpoint_url"]
            missing = [k for k in required if k not in body]
            if missing:
                raise HTTPException(status_code=400, detail=f"Missing required fields: {', '.join(missing)}")
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="register_participant",
                payload={"participant": body, "api_version": "v1"},
            )
            return build_v1_response(result, "participant_registered",)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error registering participant: {e}")
            raise HTTPException(status_code=500, detail="Failed to register participant")

    async def get_participant(self, identifier: str, request: Request):
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_participant",
                payload={"identifier": identifier, "api_version": "v1"},
            )
            if not result or not result.get("success"):
                raise HTTPException(status_code=404, detail="Participant not found")
            return build_v1_response(result, "participant_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting participant {identifier}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get participant")

    async def update_participant(self, participant_id: str, request: Request):
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_participant",
                payload={"participant_id": participant_id, "updates": body, "api_version": "v1"},
            )
            return build_v1_response(result, "participant_updated")
        except Exception as e:
            logger.error(f"Error updating participant {participant_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to update participant")

    async def get_participant_by_id(self, participant_id: str, request: Request):
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_participant",
                payload={"participant_id": participant_id, "api_version": "v1"},
            )
            if not result or not result.get("success"):
                raise HTTPException(status_code=404, detail="Participant not found")
            return build_v1_response(result, "participant_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting participant by id {participant_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get participant")

    async def resolve_participant(self, request: Request):
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            identifier = body.get("identifier")
            if not identifier:
                raise HTTPException(status_code=400, detail="identifier is required")
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="resolve_participant",
                payload={"identifier": identifier, "api_version": "v1"},
            )
            if not result or not result.get("success"):
                raise HTTPException(status_code=404, detail="Participant not found or inactive")
            return build_v1_response(result, "participant_resolved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resolving participant: {e}")
            raise HTTPException(status_code=500, detail="Failed to resolve participant")


def create_network_routing_router(role_detector: HTTPRoleDetector, permission_guard: APIPermissionGuard, message_router: MessageRouter) -> APIRouter:
    endpoints = NetworkRoutingEndpointsV1(role_detector, permission_guard, message_router)
    return endpoints.router
