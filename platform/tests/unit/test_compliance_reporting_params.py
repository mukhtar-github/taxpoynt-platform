import asyncio
import pytest
from types import SimpleNamespace
from starlette.requests import Request

from platform.backend.api_gateway.api_versions.v1.si_endpoints.compliance_endpoints import ComplianceEndpointsV1
from platform.backend.api_gateway.role_routing.models import HTTPRoutingContext
from platform.backend.api_gateway.role_routing.models import PlatformRole


class DummyRoleDetector:
    async def detect_role_context(self, request):
        return HTTPRoutingContext(
            user_id="user-1",
            organization_id="org-1",
            platform_role=PlatformRole.SYSTEM_INTEGRATOR,
        )


class DummyPermissionGuard:
    async def check_endpoint_permission(self, context, path, method):
        return True


class DummyMessageRouter:
    def __init__(self):
        self.last_call = None

    async def route_message(self, service_role, operation, payload):
        self.last_call = {
            "service_role": service_role,
            "operation": operation,
            "payload": payload,
        }
        return {"ok": True}


def make_request_with_query(query: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/si/compliance/reports/transactions",
        "headers": [],
        "query_string": query.encode("utf-8"),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_reports_forward_org_and_dates():
    detector = DummyRoleDetector()
    guard = DummyPermissionGuard()
    router = DummyMessageRouter()

    endpoints = ComplianceEndpointsV1(detector, guard, router)

    # Create context explicitly to bypass Depends in direct call
    context = HTTPRoutingContext(user_id="user-1", platform_role=PlatformRole.SYSTEM_INTEGRATOR)

    req = make_request_with_query(
        "organization_id=11111111-1111-1111-1111-111111111111&start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59&include_metrics=true"
    )

    await endpoints.get_transaction_compliance_report(
        request=req,
        organization_id="11111111-1111-1111-1111-111111111111",
        start_date="2024-01-01T00:00:00",
        end_date="2024-01-31T23:59:59",
        include_metrics=True,
        context=context,
    )

    assert router.last_call is not None
    payload = router.last_call["payload"]
    assert payload.get("organization_id") == "11111111-1111-1111-1111-111111111111"
    assert payload.get("start_date") == "2024-01-01T00:00:00"
    assert payload.get("end_date") == "2024-01-31T23:59:59"
    assert payload.get("include_metrics") is True


@pytest.mark.asyncio
async def test_onboarding_report_forward_org():
    detector = DummyRoleDetector()
    guard = DummyPermissionGuard()
    router = DummyMessageRouter()

    endpoints = ComplianceEndpointsV1(detector, guard, router)
    context = HTTPRoutingContext(user_id="user-1", platform_role=PlatformRole.SYSTEM_INTEGRATOR)
    req = make_request_with_query("")

    await endpoints.get_onboarding_report(
        request=req,
        organization_id="22222222-2222-2222-2222-222222222222",
        context=context,
    )

    assert router.last_call is not None
    payload = router.last_call["payload"]
    assert payload.get("organization_id") == "22222222-2222-2222-2222-222222222222"

