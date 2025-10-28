"""
Day 8 validation: synthetic observability checks.

These tests send controlled requests through the ObservabilityMiddleware
to ensure alerting metrics fire for business critical paths.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.testclient import TestClient

from core_platform.monitoring.fastapi_middleware import ObservabilityMiddleware


class StubPrometheusIntegration:
    """Capture recorded metrics for assertions."""

    def __init__(self) -> None:
        self.calls: List[Tuple[str, float, Dict[str, str]]] = []

    def record_metric(self, name: str, value: float, labels: Dict[str, str]) -> None:
        self.calls.append((name, value, labels))


def test_observability_middleware_records_firs_threshold(monkeypatch):
    """AAA: synthetic FIRS request should produce metrics + alert payload."""
    prometheus_stub = StubPrometheusIntegration()
    firs_events: List[Dict[str, Any]] = []

    async def fake_record_firs_request(**payload: Any) -> None:
        firs_events.append(payload)

    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setattr(
        "core_platform.monitoring.fastapi_middleware.get_prometheus_integration",
        lambda: prometheus_stub,
    )
    monkeypatch.setattr(
        "core_platform.monitoring.fastapi_middleware.record_firs_request",
        fake_record_firs_request,
    )

    app = FastAPI(middleware=[Middleware(ObservabilityMiddleware, collect_traces=False)])

    @app.get("/api/v1/firs/status")
    async def firs_status():
        return {"status": "ok"}

    client = TestClient(app)

    response = client.get("/api/v1/firs/status", headers={"X-Customer-Id": "tenant-123"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    recorded_names = {name for name, _, _ in prometheus_stub.calls}
    assert "taxpoynt_http_requests_total" in recorded_names
    assert "taxpoynt_http_request_duration_seconds" in recorded_names

    http_total = next(call for call in prometheus_stub.calls if call[0] == "taxpoynt_http_requests_total")
    assert http_total[2]["endpoint"] == "/api/v1/firs/status"
    assert http_total[2]["status_code"] == "200"
    assert http_total[2]["service_role"] == "app_services"

    assert firs_events, "FIRS synthetic alert should be recorded"
    firs_payload = firs_events[0]
    assert firs_payload["endpoint"] == "/api/v1/firs/status"
    assert firs_payload["status_code"] == 200
    assert firs_payload["operation"] == "get_request"
