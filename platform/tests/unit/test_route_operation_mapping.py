import os
import sys
import asyncio
from pathlib import Path

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_route_operation_mapping_subset_no_missing(monkeypatch):
    """Contract test: route→operation mapping for critical APP/SI modules.

    Builds the main gateway router, extracts operations used by handlers,
    registers a mock service advertising the target subset of operations,
    and asserts those are not missing according to the gateway validator.
    """
    # Lazy imports to ensure adjusted sys.path is effective
    from api_gateway.main_gateway_router import MainGatewayRouter
    from api_gateway.api_versions.version_coordinator import APIVersionCoordinator
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    from api_gateway.role_routing.permission_guard import APIPermissionGuard
    from core_platform.messaging.message_router import MessageRouter, ServiceRole

    # Build message router and coordinator
    msg_router = MessageRouter()
    version_coord = APIVersionCoordinator(msg_router)

    # Build gateway
    gateway = MainGatewayRouter(
        role_detector=HTTPRoleDetector(),
        permission_guard=APIPermissionGuard(app=None),
        message_router=msg_router,
        version_coordinator=version_coord,
    )

    # First scan handlers to discover used ops and route map
    report = gateway.validate_route_operation_mapping(fail_fast=False)
    route_map = report.get("route_map", {})

    # Select target modules: APP invoices + FIRS webhooks; SI organizations + ERP integrations
    target_prefixes = (
        "/api/v1/app/invoices",
        "/api/v1/webhooks/firs",
        "/api/v1/si/organizations",
        "/api/v1/si/integrations/erp",
    )

    target_ops = set()
    for path, ops in route_map.items():
        if any(path.startswith(pref) for pref in target_prefixes):
            for op in ops:
                target_ops.add(op)

    # Sanity check: we should have collected some operations
    assert target_ops, "No operations discovered for target route groups"

    # Register a mock APP service advertising these operations
    async def _register_ops():
        await msg_router.register_service(
            service_name="mock_app_service",
            service_role=ServiceRole.ACCESS_POINT_PROVIDER,
            metadata={"operations": sorted(list(target_ops))},
        )

    asyncio.run(_register_ops())

    # Re-scan to get known_ops and assert all target_ops are covered
    report2 = gateway.validate_route_operation_mapping(fail_fast=False)
    known_ops = set(report2.get("known_ops", []))
    missing_subset = target_ops - known_ops
    assert not missing_subset, f"Missing mapped operations for target modules: {sorted(list(missing_subset))}"

