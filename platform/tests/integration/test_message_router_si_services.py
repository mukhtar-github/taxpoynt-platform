import os
import sys
import asyncio
from pathlib import Path

import pytest

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_si_message_router_mappings_basic():
    from core_platform.messaging.message_router import MessageRouter, ServiceRole
    from si_services import SIServiceRegistry

    router = MessageRouter()
    reg = SIServiceRegistry(router)
    endpoints = await reg.initialize_services()
    assert isinstance(endpoints, dict)

    # Banking (registered)
    result = await router.route_message(
        service_role=ServiceRole.SYSTEM_INTEGRATOR,
        operation="list_open_banking_connections",
        payload={"si_id": "00000000-0000-0000-0000-000000000001", "filters": {}}
    )
    assert result.get("success") is True

    # Organization CRUD (registered)
    result = await router.route_message(
        service_role=ServiceRole.SYSTEM_INTEGRATOR,
        operation="create_organization",
        payload={"organization_data": {"name": "Test Org"}}
    )
    assert result.get("success") is True
    org_id = result.get("organization", {}).get("id")
    assert org_id

    # Validation (registered)
    result = await router.route_message(
        service_role=ServiceRole.SYSTEM_INTEGRATOR,
        operation="validate_bvn",
        payload={"bvn": "12345678901"}
    )
    assert result.get("success") is True

    # Reconciliation (registered)
    result = await router.route_message(
        service_role=ServiceRole.SYSTEM_INTEGRATOR,
        operation="save_reconciliation_configuration",
        payload={"si_id": "si_1", "config": {"rules": []}}
    )
    assert result.get("success") is True

