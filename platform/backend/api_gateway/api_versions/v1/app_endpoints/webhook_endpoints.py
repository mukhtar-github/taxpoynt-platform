"""APP Webhook Endpoints - FIRS Notifications"""

import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status

from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.messaging.message_router import MessageRouter
from core_platform.authentication.role_manager import PlatformRole, RoleScope
from api_gateway.api_versions.v1.webhook_endpoints.firs_webhook import create_firs_webhook_router

logger = logging.getLogger(__name__)


def create_app_webhook_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter,
) -> APIRouter:
    """Create APP webhook router that proxies to the shared FIRS webhook handler."""

    router = APIRouter(prefix="/webhooks", tags=["APP Webhooks"])

    async def _require_app_role(request: Request) -> HTTPRoutingContext:
        context = await role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Point Provider role required")
        if not await permission_guard.check_endpoint_permission(
            context=context,
            route=str(request.url.path),
            method=request.method,
            required_scope=RoleScope.ACCESS_POINT_PROVIDER,
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied for webhook endpoint")
        return context

    firs_webhook_router = create_firs_webhook_router(message_router)
    router.include_router(
        firs_webhook_router,
        prefix="/firs",
        tags=["FIRS Webhooks"],
        dependencies=[Depends(_require_app_role)],
    )

    logger.info("APP webhook router (FIRS) initialized")
    return router
