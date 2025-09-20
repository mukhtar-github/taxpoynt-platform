"""
Demo Utilities (HYBRID)
=======================
Endpoints to help seed external systems for demos (e.g., Odoo).
These are HYBRID-protected and intended for local/dev usage.
"""
import asyncio
import os
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from core_platform.authentication.role_manager import PlatformRole
from api_gateway.utils.v1_response import build_v1_response

logger = logging.getLogger(__name__)


class OdooSeedRequest(BaseModel):
    crm: int = Field(5, ge=0, description="Number of CRM opportunities to create")
    invoices: int = Field(3, ge=0, description="Number of posted invoices to create")
    ecom: int = Field(3, ge=0, description="Number of online orders to create")
    pos: int = Field(0, ge=0, description="Number of POS orders to create (requires ODOO_POS_SESSION_ID)")


def create_demo_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
) -> APIRouter:
    router = APIRouter(prefix="/demo", tags=["Demo Utilities"])

    async def _require_hybrid_role(request: Request) -> HTTPRoutingContext:
        context = await role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.HYBRID):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hybrid role required")
        if not await permission_guard.check_endpoint_permission(
            context, f"v1/hybrid{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return context

    @router.post("/seed-odoo")
    async def seed_odoo_demo(
        payload: OdooSeedRequest,
        context: HTTPRoutingContext = Depends(_require_hybrid_role),
    ):
        """Seed Odoo with demo data using the local seeding helpers.

        Reads Odoo credentials from environment. If a target Odoo module
        is unavailable, the seeder skips it and proceeds with others.
        """
        try:
            # Feature flag / environment guard
            enabled = str(os.getenv("DEMO_SEEDER_ENABLED", "false")).lower() in ("1", "true", "yes", "on")
            environment = str(os.getenv("ENVIRONMENT", "development")).lower()
            is_admin = context.has_role(PlatformRole.PLATFORM_ADMIN) if context else False
            if environment == "production" and not (enabled or is_admin):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo seeder disabled in production")

            # Import lazily to avoid hard dependency when unused
            from scripts import odoo_seed_demo_data as seeder  # type: ignore

            def _run():
                env = seeder._get_env()
                odoo = seeder.connect(env)
                return {
                    "crm": seeder.seed_crm(odoo, payload.crm),
                    "invoices": seeder.seed_invoices(odoo, payload.invoices),
                    "ecom": seeder.seed_ecommerce_orders(odoo, payload.ecom),
                    "pos": seeder.seed_pos_orders(odoo, payload.pos, env.get("pos_session_id")),
                }

            results = await asyncio.to_thread(_run)
            return build_v1_response({"seeded": results}, action="seed_odoo_demo")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Odoo seeding failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to seed Odoo demo data")

    return router
