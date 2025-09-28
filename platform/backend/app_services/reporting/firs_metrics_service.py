"""Aggregates FIRS Prometheus metrics for APP dashboards."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from core_platform.monitoring import get_prometheus_integration


@dataclass
class FIRSMetricsSnapshot:
    available: bool
    generated_at: str
    requests: List[Dict[str, Any]]
    latency: List[Dict[str, Any]]
    totals: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "generated_at": self.generated_at,
            "requests": self.requests,
            "latency": self.latency,
            "totals": self.totals,
        }


class FIRSMetricsService:
    """Collects high-level FIRS request metrics from Prometheus."""

    def __init__(self, prometheus_integration=None) -> None:
        self.prometheus = prometheus_integration or get_prometheus_integration()

    async def get_metrics_snapshot(self) -> Dict[str, Any]:
        timestamp = datetime.now(timezone.utc).isoformat()
        if not self.prometheus:
            return FIRSMetricsSnapshot(
                available=False,
                generated_at=timestamp,
                requests=[],
                latency=[],
                totals={"requests": 0, "error_rate": 0.0},
            ).to_dict()

        requests = self._summarize_requests()
        latency = self._summarize_latency()

        total_requests = sum(item.get("count", 0) for item in requests)
        total_errors = sum(
            item.get("count", 0)
            for item in requests
            if int(item.get("status_code", 0)) >= 400
        )
        error_rate = (total_errors / total_requests) if total_requests else 0.0

        snapshot = FIRSMetricsSnapshot(
            available=True,
            generated_at=timestamp,
            requests=requests,
            latency=latency,
            totals={
                "requests": total_requests,
                "errors": total_errors,
                "error_rate": error_rate,
            },
        )
        return snapshot.to_dict()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_metric(self, name: str):
        return getattr(self.prometheus, "prometheus_metrics", {}).get(name)

    def _summarize_requests(self) -> List[Dict[str, Any]]:
        counter = self._get_metric("taxpoynt_firs_requests_total")
        if not counter:
            return []

        summary: Dict[Tuple[str, str, str], float] = defaultdict(float)
        for metric in counter.collect():
            for sample in metric.samples:
                if not sample.name.endswith("_total"):
                    continue
                endpoint = sample.labels.get("endpoint", "unknown")
                operation = sample.labels.get("operation", "unknown")
                status_code = sample.labels.get("status_code", "unknown")
                key = (endpoint, operation, status_code)
                summary[key] += float(sample.value)

        results = [
            {
                "endpoint": endpoint,
                "operation": operation,
                "status_code": status_code,
                "count": count,
            }
            for (endpoint, operation, status_code), count in summary.items()
        ]
        results.sort(key=lambda item: item["count"], reverse=True)
        return results

    def _summarize_latency(self) -> List[Dict[str, Any]]:
        histogram = self._get_metric("taxpoynt_firs_request_duration_seconds")
        if not histogram:
            return []

        bucket_map: Dict[Tuple[Tuple[str, str], Tuple[str, str]], List[Tuple[float, float]]] = defaultdict(list)
        sums: Dict[Tuple[Tuple[str, str], Tuple[str, str]], float] = {}
        counts: Dict[Tuple[Tuple[str, str], Tuple[str, str]], float] = {}

        for metric in histogram.collect():
            for sample in metric.samples:
                labels = dict(sample.labels)
                endpoint = labels.get("endpoint", "unknown")
                operation = labels.get("operation", "unknown")
                key = (("endpoint", endpoint), ("operation", operation))

                if sample.name.endswith("_bucket"):
                    le = labels.get("le", "+Inf")
                    upper = float(le) if le != "+Inf" else float("inf")
                    bucket_map[key].append((upper, float(sample.value)))
                elif sample.name.endswith("_sum"):
                    sums[key] = float(sample.value)
                elif sample.name.endswith("_count"):
                    counts[key] = float(sample.value)

        latency_stats: List[Dict[str, Any]] = []
        for key, buckets in bucket_map.items():
            count = counts.get(key, 0.0)
            if count <= 0:
                continue
            total = sums.get(key, 0.0)
            buckets.sort(key=lambda item: item[0])

            labels = dict(key)
            latency_stats.append(
                {
                    "endpoint": labels.get("endpoint", "unknown"),
                    "operation": labels.get("operation", "unknown"),
                    "average_duration": total / count if count else 0.0,
                    "p50": self._estimate_quantile(buckets, count, 0.5),
                    "p95": self._estimate_quantile(buckets, count, 0.95),
                    "count": count,
                }
            )

        latency_stats.sort(key=lambda item: item["average_duration"], reverse=True)
        return latency_stats

    @staticmethod
    def _estimate_quantile(
        buckets: List[Tuple[float, float]], total_count: float, quantile: float
    ) -> Optional[float]:
        if total_count <= 0 or not buckets:
            return None

        target = total_count * quantile
        for upper_bound, cumulative in buckets:
            if cumulative >= target:
                return None if upper_bound == float("inf") else upper_bound
        return None


__all__ = ["FIRSMetricsService", "FIRSMetricsSnapshot"]
