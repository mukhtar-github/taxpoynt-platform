"""Unit tests for APIPermissionGuard.require_permissions helper."""

import pytest
from fastapi import FastAPI, HTTPException
from starlette.requests import Request

from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.role_routing.models import HTTPRoutingContext, PlatformRole


def _make_request(path: str = "/test") -> Request:
    async def receive() -> dict:
        return {"type": "http.request"}

    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": [],
    }
    return Request(scope, receive)


class _StubRoleDetector:
    def __init__(self, context: HTTPRoutingContext) -> None:
        self._context = context

    async def detect_role_context(self, request: Request) -> HTTPRoutingContext:
        return self._context


@pytest.mark.asyncio
async def test_require_permissions_success_sets_context_state():
    context = HTTPRoutingContext(
        user_id="hybrid-user",
        platform_role=PlatformRole.HYBRID,
        permissions=["hybrid_access"],
    )
    guard = APIPermissionGuard(FastAPI(), role_detector=_StubRoleDetector(context))

    request = _make_request()
    result = await guard.require_permissions(
        request,
        required_roles=[PlatformRole.HYBRID],
        required_permission="hybrid_access",
    )

    assert result is context
    assert getattr(request.state, "routing_context") is context


@pytest.mark.asyncio
async def test_require_permissions_missing_user_raises_401():
    context = HTTPRoutingContext(user_id=None, platform_role=PlatformRole.HYBRID)
    guard = APIPermissionGuard(FastAPI(), role_detector=_StubRoleDetector(context))

    with pytest.raises(HTTPException) as exc:
        await guard.require_permissions(_make_request())

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_require_permissions_wrong_role_raises_403():
    context = HTTPRoutingContext(
        user_id="si-user",
        platform_role=PlatformRole.SYSTEM_INTEGRATOR,
    )
    guard = APIPermissionGuard(FastAPI(), role_detector=_StubRoleDetector(context))

    with pytest.raises(HTTPException) as exc:
        await guard.require_permissions(
            _make_request(),
            required_roles=[PlatformRole.HYBRID],
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_permissions_missing_permission_raises_403():
    context = HTTPRoutingContext(
        user_id="hybrid-user",
        platform_role=PlatformRole.HYBRID,
        permissions=["other_permission"],
    )
    guard = APIPermissionGuard(FastAPI(), role_detector=_StubRoleDetector(context))

    with pytest.raises(HTTPException) as exc:
        await guard.require_permissions(
            _make_request(),
            required_permission="hybrid_access",
        )

    assert exc.value.status_code == 403
