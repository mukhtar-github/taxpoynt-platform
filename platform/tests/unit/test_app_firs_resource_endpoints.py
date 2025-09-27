"""Unit tests for APP FIRS resource endpoints."""

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from api_gateway.api_versions.v1.app_endpoints.firs_integration_endpoints import (
    FIRSIntegrationEndpointsV1,
)
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole


def _build_request(headers=None) -> Request:
    header_items = []
    if headers:
        for key, value in headers.items():
            header_items.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/app/firs/validation/rules",
        "headers": header_items,
    }
    return Request(scope)


class _StubRoleDetector:
    async def detect_role_context(self, request):  # pragma: no cover - not used directly in tests
        return HTTPRoutingContext(
            user_id="tester",
            platform_role=PlatformRole.ACCESS_POINT_PROVIDER,
            service_role=ServiceRole.ACCESS_POINT_PROVIDER,
            is_authenticated=True,
        )


class _StubPermissionGuard:
    async def check_endpoint_permission(self, context, path, method):  # pragma: no cover - stub always grants
        return True


class _RecordingMessageRouter:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def route_message(self, service_role, operation, payload):
        self.calls.append({
            "service_role": service_role,
            "operation": operation,
            "payload": payload,
        })
        return self.response


def _build_context(role: PlatformRole = PlatformRole.ACCESS_POINT_PROVIDER) -> HTTPRoutingContext:
    return HTTPRoutingContext(
        user_id="tester",
        platform_role=role,
        service_role=ServiceRole.ACCESS_POINT_PROVIDER,
        is_authenticated=True,
    )


@pytest.mark.asyncio
async def test_validation_rules_returns_etag_and_last_modified_headers():
    response_payload = {
        "operation": "get_firs_validation_rules",
        "success": True,
        "data": {
            "resources": {"currencies": ["NGN"]},
            "metadata": {
                "etag": "abc123",
                "last_modified": "2024-10-10T12:00:00Z",
            },
        },
    }
    router = _RecordingMessageRouter(response_payload)
    endpoints = FIRSIntegrationEndpointsV1(_StubRoleDetector(), _StubPermissionGuard(), router)

    request = _build_request()
    context = _build_context()

    response = await endpoints.get_firs_validation_rules(request, context)

    assert isinstance(response, JSONResponse)
    assert response.status_code == 200
    # Headers should include quotes around ETag and RFC 2822 timestamp
    assert response.headers.get("ETag") == '"abc123"'
    assert "GMT" in response.headers.get("Last-Modified", ""), "Last-Modified header should be RFC 2822 formatted"


@pytest.mark.asyncio
async def test_validation_rules_returns_304_when_etag_matches_request():
    response_payload = {
        "operation": "get_firs_validation_rules",
        "success": True,
        "data": {
            "resources": {"currencies": ["NGN"]},
            "metadata": {
                "etag": "cache-tag",
                "last_modified": "2024-09-01T09:30:00Z",
            },
        },
    }
    router = _RecordingMessageRouter(response_payload)
    endpoints = FIRSIntegrationEndpointsV1(_StubRoleDetector(), _StubPermissionGuard(), router)

    request = _build_request({"if-none-match": '"cache-tag"'})
    context = _build_context()

    response = await endpoints.get_firs_validation_rules(request, context)

    assert isinstance(response, Response)
    assert response.status_code == 304
    assert response.headers.get("ETag") == '"cache-tag"'


@pytest.mark.asyncio
async def test_validation_rules_returns_304_when_if_modified_since_is_recent():
    metadata = {
        "etag": "etag-1",
        "last_modified": "2024-11-05T08:00:00Z",
    }
    response_payload = {
        "operation": "get_firs_validation_rules",
        "success": True,
        "data": {"resources": {}, "metadata": metadata},
    }
    router = _RecordingMessageRouter(response_payload)
    endpoints = FIRSIntegrationEndpointsV1(_StubRoleDetector(), _StubPermissionGuard(), router)

    # Build request using Last-Modified value returned by handler
    request = _build_request({"if-modified-since": "Tue, 05 Nov 2024 08:00:00 GMT"})
    context = _build_context()

    response = await endpoints.get_firs_validation_rules(request, context)

    assert isinstance(response, Response)
    assert response.status_code == 304
    assert response.headers.get("Last-Modified") == "Tue, 05 Nov 2024 08:00:00 GMT"


@pytest.mark.asyncio
async def test_admin_refresh_marks_manual_metadata_and_sets_force_refresh():
    response_payload = {
        "operation": "refresh_firs_resources",
        "success": True,
        "data": {"resources": {}, "metadata": {}},
    }
    router = _RecordingMessageRouter(response_payload)
    endpoints = FIRSIntegrationEndpointsV1(_StubRoleDetector(), _StubPermissionGuard(), router)

    context = _build_context(role=PlatformRole.PLATFORM_ADMIN)

    response = await endpoints.admin_refresh_firs_resources(context)

    assert router.calls, "Message router should be invoked"
    call = router.calls[0]
    assert call["service_role"] == ServiceRole.ACCESS_POINT_PROVIDER
    assert call["operation"] == "refresh_firs_resources"
    assert call["payload"].get("force_refresh") is True
    assert call["payload"].get("triggered_by") == "admin"

    assert response.action == "firs_resources_admin_refreshed"
    metadata = response.data["data"]["metadata"]
    assert metadata["manual_refresh"] is True
    assert metadata["triggered_by"] == "admin"
