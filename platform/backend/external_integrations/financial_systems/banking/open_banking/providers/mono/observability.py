"""Shared observability helpers for the Mono banking pipeline."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, Optional

from core_platform.monitoring.prometheus_integration import (
    PrometheusMetric,
    PrometheusMetricsType,
    get_prometheus_integration,
)

logger = logging.getLogger(__name__)

_METRICS_REGISTERED = False
_FAILURE_COUNTS: Dict[str, int] = defaultdict(int)

FAILURE_ALERT_THRESHOLD = 5
LATENCY_ALERT_SECONDS = 2.0

_PROVIDER_LABELS = {"provider": "mono"}
_STAGE_METRIC = "taxpoynt_mono_pipeline_stage_seconds"
_ERROR_METRIC = "taxpoynt_mono_pipeline_errors_total"
_ZERO_TX_METRIC = "taxpoynt_mono_pipeline_zero_transactions_total"


def _ensure_metrics():
    prom = get_prometheus_integration()
    if not prom:
        return None

    global _METRICS_REGISTERED
    if not _METRICS_REGISTERED:
        try:
            prom.register_metric(
                PrometheusMetric(
                    name=_STAGE_METRIC,
                    metric_type=PrometheusMetricsType.HISTOGRAM,
                    description="Mono pipeline stage durations in seconds",
                    labels=["provider", "stage", "outcome"],
                    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
                )
            )
            prom.register_metric(
                PrometheusMetric(
                    name=_ERROR_METRIC,
                    metric_type=PrometheusMetricsType.COUNTER,
                    description="Mono pipeline error counts by stage and reason",
                    labels=["provider", "stage", "reason"],
                )
            )
            prom.register_metric(
                PrometheusMetric(
                    name=_ZERO_TX_METRIC,
                    metric_type=PrometheusMetricsType.COUNTER,
                    description="Mono pipeline runs with zero fetched transactions",
                    labels=["provider"],
                )
            )
        except Exception:  # pragma: no cover - defensive registration guard
            logger.debug("Failed to register Mono Prometheus metrics", exc_info=True)
        finally:
            _METRICS_REGISTERED = True

    return prom


def record_stage_duration(stage: str, outcome: str, duration: float) -> None:
    prom = _ensure_metrics()
    if not prom:
        return
    try:
        prom.record_metric(
            _STAGE_METRIC,
            duration,
            {**_PROVIDER_LABELS, "stage": stage, "outcome": outcome},
        )
    except Exception:  # pragma: no cover - metrics should not break flow
        logger.debug("Failed to record Mono stage duration", exc_info=True)


def record_stage_error(stage: str, reason: str) -> None:
    prom = _ensure_metrics()
    if not prom:
        return
    try:
        prom.record_metric(_ERROR_METRIC, 1, {**_PROVIDER_LABELS, "stage": stage, "reason": reason})
    except Exception:  # pragma: no cover
        logger.debug("Failed to record Mono stage error metric", exc_info=True)


def record_zero_transactions() -> None:
    prom = _ensure_metrics()
    if not prom:
        return
    try:
        prom.record_metric(_ZERO_TX_METRIC, 1, _PROVIDER_LABELS)
    except Exception:  # pragma: no cover
        logger.debug("Failed to record Mono zero transaction metric", exc_info=True)


def register_failure(account_id: str) -> int:
    _FAILURE_COUNTS[account_id] += 1
    return _FAILURE_COUNTS[account_id]


def reset_failure(account_id: str) -> None:
    _FAILURE_COUNTS.pop(account_id, None)


def latency_sla_breached(duration: float) -> bool:
    return duration > LATENCY_ALERT_SECONDS


def reason_from_exception(exc: BaseException) -> str:
    return exc.__class__.__name__


__all__ = [
    "FAILURE_ALERT_THRESHOLD",
    "LATENCY_ALERT_SECONDS",
    "record_stage_duration",
    "record_stage_error",
    "record_zero_transactions",
    "register_failure",
    "reset_failure",
    "latency_sla_breached",
    "reason_from_exception",
]
