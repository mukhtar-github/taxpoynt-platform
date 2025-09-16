import asyncio
import pytest


@pytest.mark.asyncio
async def test_metrics_smoke_contract():
    from platform.backend.core_platform.monitoring.metrics_aggregator import (
        metrics_aggregator, ServiceRole, MetricType,
    )

    # Collect a simple metric point and fetch current metrics
    ok = await metrics_aggregator.collect_metric_point(
        name="smoke_test_metric",
        value=1,
        service_role=ServiceRole.CORE_PLATFORM,
        service_name="unit_test",
        metric_type=MetricType.GAUGE,
        tags={"scope": "smoke"},
    )
    assert ok is True

    current = await metrics_aggregator.get_current_metrics()
    assert isinstance(current, list)
    # Ensure our metric appears or structure matches
    if current:
        sample = current[-1]
        assert "name" in sample and "service_role" in sample and "value" in sample


@pytest.mark.asyncio
async def test_health_smoke_contract():
    from platform.backend.core_platform.messaging.async_health_checker import (
        AsyncHealthCheckManager, HealthCheckConfig,
    )

    mgr = AsyncHealthCheckManager()

    async def ok_check():
        return "ok"

    mgr.register_service("smoke_service", ok_check, HealthCheckConfig(check_interval=1, timeout=1))
    # Force a single immediate check and then read status
    metrics = await mgr.check_service_now("smoke_service")
    assert metrics is not None
    status = await mgr.get_health_status()
    assert "overall_status" in status and "services" in status
    assert "smoke_service" in status["services"]


@pytest.mark.asyncio
async def test_message_router_stats_smoke_contract():
    from platform.backend.core_platform.messaging.message_router import MessageRouter

    router = MessageRouter()
    stats = await router.get_routing_stats()
    assert isinstance(stats, dict)
    for key in ("routing_stats", "service_endpoints", "routing_rules", "active_routes"):
        assert key in stats

