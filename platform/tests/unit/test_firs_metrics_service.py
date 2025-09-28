import asyncio
from types import SimpleNamespace

import pytest
from prometheus_client import Counter, Histogram

from app_services.reporting.firs_metrics_service import FIRSMetricsService


@pytest.mark.asyncio
async def test_firs_metrics_service_summarizes_metrics():
    counter = Counter(
        "taxpoynt_firs_requests_total",
        "",
        ["service_name", "endpoint", "status_code", "operation"],
        registry=None,
    )
    histogram = Histogram(
        "taxpoynt_firs_request_duration_seconds",
        "",
        ["endpoint", "operation"],
        registry=None,
    )

    counter.labels("app", "/firs/submit", "200", "post_request").inc(5)
    counter.labels("app", "/firs/submit", "500", "post_request").inc(1)

    for _ in range(4):
        histogram.labels("/firs/submit", "post_request").observe(0.2)
    histogram.labels("/firs/submit", "post_request").observe(1.0)

    integration = SimpleNamespace(
        prometheus_metrics={
            "taxpoynt_firs_requests_total": counter,
            "taxpoynt_firs_request_duration_seconds": histogram,
        }
    )

    service = FIRSMetricsService(prometheus_integration=integration)
    snapshot = await service.get_metrics_snapshot()

    assert snapshot["available"] is True
    assert snapshot["totals"]["requests"] == 6
    assert snapshot["totals"]["errors"] == 1
    assert snapshot["requests"]
    assert snapshot["latency"]

