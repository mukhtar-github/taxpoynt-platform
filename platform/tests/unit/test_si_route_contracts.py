"""
Contract tests for SI route→operation mappings and registry coverage.

Ensures every SI endpoint operation discovered in the gateway has a
corresponding registered operation in the MessageRouter after the
SI service registry initializes.
"""
import os
import sys


def _prepare_path():
    CURRENT_DIR = os.path.dirname(__file__)
    BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend"))
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)


def test_all_si_routes_have_registered_handlers():
    _prepare_path()

    from api_gateway.main_gateway_router import MainGatewayRouter
    from api_gateway.api_versions.version_coordinator import APIVersionCoordinator
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    from api_gateway.role_routing.permission_guard import APIPermissionGuard
    from core_platform.messaging.message_router import MessageRouter
    from si_services import SIServiceRegistry

    # Build router and initialize SI services
    router = MessageRouter()
    version_coord = APIVersionCoordinator(router)
    si_reg = SIServiceRegistry(router)

    # Initialize services (registers operations with metadata)
    import asyncio
    asyncio.get_event_loop().run_until_complete(si_reg.initialize_services())

    # Build gateway and validate mapping
    gateway = MainGatewayRouter(
        role_detector=HTTPRoleDetector(),
        permission_guard=APIPermissionGuard(app=None),
        message_router=router,
        version_coordinator=version_coord,
    )

    report = gateway.validate_route_operation_mapping(fail_fast=False)

    # Collect SI-only used ops from route_map
    route_map = report.get("route_map", {})
    used_si_ops = set()
    for path, ops in route_map.items():
        if path.startswith("/api/v1/si/"):
            used_si_ops.update(ops)

    assert used_si_ops, "No SI operations discovered from SI routes"

    known_ops = set(report.get("known_ops", []))
    missing = sorted(op for op in used_si_ops if op not in known_ops)
    assert not missing, f"Missing SI operations in registry metadata: {missing}"


def test_strict_mode_raises_on_unknown_op(monkeypatch):
    """When strict mode is enabled, unknown operations must raise."""
    _prepare_path()

    monkeypatch.setenv("ROUTER_STRICT_OPS", "true")

    from core_platform.messaging.message_router import MessageRouter, ServiceRole
    import pytest
    import asyncio

    router = MessageRouter()

    with pytest.raises(RuntimeError):
        asyncio.get_event_loop().run_until_complete(
            router.route_message(ServiceRole.SYSTEM_INTEGRATOR, "totally_unknown_op", {})
        )

