import pytest
from fastapi import HTTPException
from api_gateway.api_versions.v1.si_endpoints.utils.si_http import route_or_http


class DummyRouter:
    def __init__(self, result=None, exc: Exception | None = None):
        self._result = result
        self._exc = exc

    async def route_message(self, *, service_role, operation, payload):
        if self._exc:
            raise self._exc
        return self._result


@pytest.mark.asyncio
async def test_route_or_http_maps_value_error_to_400():
    r = DummyRouter(exc=ValueError("bad input"))
    with pytest.raises(HTTPException) as ei:
        await route_or_http(r, service_role="si", operation="op", payload={})
    assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_route_or_http_maps_timeout_to_504():
    r = DummyRouter(exc=TimeoutError("timeout"))
    with pytest.raises(HTTPException) as ei:
        await route_or_http(r, service_role="si", operation="op", payload={})
    assert ei.value.status_code == 504


@pytest.mark.asyncio
async def test_route_or_http_maps_unsuccessful_result_not_found():
    r = DummyRouter(result={"success": False, "error": {"error_code": "not_found", "message": "missing"}})
    with pytest.raises(HTTPException) as ei:
        await route_or_http(r, service_role="si", operation="op", payload={})
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_route_or_http_passes_success_through():
    data = {"success": True, "data": {"ok": True}}
    r = DummyRouter(result=data)
    out = await route_or_http(r, service_role="si", operation="op", payload={})
    assert out == data

