"""Async integration smoke tests for APP reporting services.

These tests exercise the reporting pipeline without a backing database to
ensure the async generators gracefully fall back to mock data while still
returning rich payloads that the API layer and UI depend on. They provide
fast feedback in CI that the transmission reports, compliance metrics, and
comprehensive dashboards remain wired together after code changes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from platform.backend.app_services import ReportingServiceManager
from platform.backend.app_services.reporting.compliance_metrics import ComplianceDataProvider
from platform.backend.app_services.reporting.transmission_reports import (
    ReportConfig,
    ReportFormat,
    TransmissionReportGenerator,
)


@pytest.mark.asyncio
async def test_transmission_report_generator_fallback_without_db() -> None:
    """Generator should produce a summary even when DB access is unavailable."""

    generator = TransmissionReportGenerator()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=2)

    config = ReportConfig(
        start_date=start,
        end_date=end,
        format=ReportFormat.JSON,
        include_details=False,
        include_charts=False,
    )

    report = await generator.generate_report(config)
    metadata = report["metadata"]
    summary = report["report_data"]["summary"]

    assert metadata["record_count"] == summary["total_transmissions"]
    assert summary["total_transmissions"] >= 0
    assert 0.0 <= summary["success_rate"] <= 100.0


@pytest.mark.asyncio
async def test_compliance_metrics_provider_uses_transmission_provider() -> None:
    """Compliance provider should surface dynamic transmission metrics."""

    provider = ComplianceDataProvider()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=1)

    metrics = await provider.get_transmission_metrics(start, end)

    assert metrics["total_transmissions"] >= metrics["successful_transmissions"]
    assert "transmission_by_hour" in metrics
    assert isinstance(metrics["retry_attempts"], int)


@pytest.mark.asyncio
async def test_reporting_manager_comprehensive_report_structure() -> None:
    """Comprehensive report should include all component sections."""

    manager = ReportingServiceManager()
    await manager.initialize_services()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=1)

    report = await manager.generate_comprehensive_report(start, end, ReportFormat.JSON)

    transmission_summary = report["transmission_report"]["report_data"]["summary"]
    assert transmission_summary["total_transmissions"] >= 0

    compliance = report["compliance_report"]
    assert "overall_status" in compliance and "overall_score" in compliance

    performance = report["performance_analysis"]
    assert "overall_score" in performance and "status" in performance

    dashboard = report["executive_dashboard"]
    assert "summary_metrics" in dashboard and "alerts" in dashboard
