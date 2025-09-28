"""Contract tests validating route operation to service mapping consistency."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from api_gateway.api_versions.version_coordinator import APIVersionCoordinator
from api_gateway.main_gateway_router import MainGatewayRouter
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from app_services import APPServiceRegistry
from si_services import SIServiceRegistry
from hybrid_services import HybridServiceRegistry
from core_platform.messaging.message_router import MessageRouter


@pytest.mark.asyncio
async def test_api_route_operations_are_backed_by_registered_services(monkeypatch):
    """Ensure every route operation declared by the gateway maps to a registered service callback."""

    # Ensure required environment secrets exist for service initialization
    monkeypatch.setenv("FIRS_WEBHOOK_SECRET", os.getenv("FIRS_WEBHOOK_SECRET", "test-secret"))
    monkeypatch.setenv("DATABASE_URL", os.getenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:"))
    monkeypatch.delenv("APP_INIT_MINIMAL", raising=False)

    message_router = MessageRouter()

    # Initialize service registries so actual callbacks/metadata are registered
    app_registry = APPServiceRegistry(message_router)
    si_registry = SIServiceRegistry(message_router)
    hybrid_registry = HybridServiceRegistry(message_router)

    await app_registry.initialize_services()
    await si_registry.initialize_services()
    await hybrid_registry.initialize_services()

    gateway = MainGatewayRouter(
        role_detector=HTTPRoleDetector(),
        permission_guard=APIPermissionGuard(app=FastAPI()),
        message_router=message_router,
        version_coordinator=APIVersionCoordinator(message_router),
    )

    report = gateway.validate_route_operation_mapping(fail_fast=False)
    missing_ops = report.get("missing_ops", [])
    assert not missing_ops, f"Route operations lacking service mappings: {missing_ops}"

    # Build a map from operation -> registered callbacks exposing that operation
    op_to_callbacks = {}
    for endpoint in message_router.service_endpoints.values():
        operations = endpoint.metadata.get("operations") or []
        for operation in operations:
            op_to_callbacks.setdefault(operation, []).append(endpoint.callback)

    for operation in report.get("used_ops", []):
        callbacks = op_to_callbacks.get(operation)
        assert callbacks, f"No service advertises operation '{operation}'"
        assert any(cb is not None for cb in callbacks), f"Operation '{operation}' has no registered callback"
