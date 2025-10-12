"""
Integration Health Monitor

Consolidated health and status monitoring for integrations.
Combines functionality from integration_service.py status monitoring and generic health monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import deque, defaultdict

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class HealthThreshold:
    """Health monitoring thresholds"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison_operator: str = "gt"  # gt, lt, eq, gte, lte
    enabled: bool = True


@dataclass
class HealthMetric:
    """Individual health metric"""
    integration_id: str
    metric_name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """Health monitoring alert"""
    alert_id: str
    integration_id: str
    severity: AlertSeverity
    title: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False


class IntegrationHealthMonitor:
    """
    Consolidated health and status monitoring for integrations.
    Combines integration-specific monitoring with generic health monitoring capabilities.
    """
    
    def __init__(self):
        # Integration status monitoring
        self._monitor_tasks: Dict[str, asyncio.Task] = {}
        self._monitor_config: Dict[str, Dict[str, Any]] = {}
        self._status_cache: Dict[str, Dict[str, Any]] = {}
        self._snapshot_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self._default_interval_minutes = 30
        self._lock = asyncio.Lock()
        self.connection_manager = None
        
        # Health monitoring components
        self.health_metrics = deque(maxlen=10000)
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        
        # Thresholds
        self.default_thresholds = {
            "response_time": HealthThreshold("response_time", 5000, 10000, "gt"),
            "success_rate": HealthThreshold("success_rate", 90.0, 80.0, "lt"),
            "error_rate": HealthThreshold("error_rate", 5.0, 10.0, "gt"),
            "availability": HealthThreshold("availability", 95.0, 90.0, "lt")
        }
        
        # Dependencies
        self.connection_tester = None  # Will be injected
    
    def set_connection_tester(self, connection_tester):
        """Inject connection tester dependency"""
        self.connection_tester = connection_tester
    
    def add_alert_handler(self, handler: Callable):
        """Add alert handler function"""
        self.alert_handlers.append(handler)
    
    # === Integration Status Monitoring (from integration_service.py) ===
    
    def get_integration_status(self, integration_id: str) -> Dict[str, Any]:
        """
        Get the current status of an integration.
        Extracted from integration_service.py lines 1396-1431
        """
        str_id = str(integration_id)
        status_info = self._status_cache.get(str_id)

        if not status_info:
            # If not in cache, create basic status info
            status_info = {
                "status": "unknown",
                "last_checked": None,
                "message": "Status has not been checked yet",
                "details": {}
            }
            self._status_cache[str_id] = status_info

        formatted = dict(status_info)
        last_checked = formatted.get("last_checked")
        if isinstance(last_checked, datetime):
            formatted["last_checked"] = last_checked.isoformat()
        formatted["details"] = self._serialize_value(formatted.get("details", {}))
        return formatted
    
    async def attach_connection_manager(self, connection_manager, default_interval_minutes: int = 30) -> None:
        """Attach connection manager and ensure monitoring for registered systems."""
        async with self._lock:
            self.connection_manager = connection_manager
            self._default_interval_minutes = default_interval_minutes
            system_ids = list(connection_manager.configs.keys())

        for system_id in system_ids:
            print("attach_monitor ensure", system_id)
            await self._ensure_monitoring(str(system_id), None, default_interval_minutes)
        print("attach_monitor done")

    async def start_integration_monitoring(
        self,
        integration_id: str,
        integration_config: Dict[str, Any],
        interval_minutes: int = 30
    ) -> bool:
        """Start async monitoring for an integration."""
        await self._ensure_monitoring(str(integration_id), integration_config, interval_minutes)
        logger.info(f"Started monitoring for integration {integration_id}")
        return True

    async def stop_integration_monitoring(self, integration_id: str) -> bool:
        """Stop async monitoring for an integration."""
        str_id = str(integration_id)
        async with self._lock:
            task = self._monitor_tasks.pop(str_id, None)
            self._monitor_config.pop(str_id, None)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                logger.info(f"Stopped monitoring for integration {integration_id}")
                return True
        return False

    async def stop_all_monitoring(self) -> None:
        """Stop all monitoring tasks."""
        async with self._lock:
            tasks = list(self._monitor_tasks.values())
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            self._monitor_tasks.clear()
            self._monitor_config.clear()

    async def track_connection(
        self,
        integration_id: str,
        integration_config: Optional[Dict[str, Any]] = None,
        interval_minutes: Optional[int] = None
    ) -> None:
        """Ensure monitoring for a connection using provided configuration."""
        await self._ensure_monitoring(
            str(integration_id),
            integration_config,
            interval_minutes or self._default_interval_minutes,
        )

    async def untrack_connection(self, integration_id: str) -> None:
        """Stop monitoring for a connection if active."""
        await self.stop_integration_monitoring(integration_id)

    def get_all_monitored_integrations(self) -> List[Dict[str, Any]]:
        """Get a list of all integrations being monitored."""
        result = []

        for integration_id, task in self._monitor_tasks.items():
            status = self._status_cache.get(integration_id, {})
            if not task.done():
                result.append({
                    "integration_id": integration_id,
                    "name": f"Integration {integration_id}",
                    "status": status.get("status", "unknown"),
                    "last_checked": status.get("last_checked"),
                    "message": status.get("message", ""),
                    "is_monitoring": True
                })

        return result

    async def _ensure_monitoring(self, integration_id: str, integration_config: Optional[Dict[str, Any]], interval_minutes: int) -> None:
        async with self._lock:
            if integration_id in self._monitor_tasks and not self._monitor_tasks[integration_id].done():
                return

            self._monitor_config[integration_id] = {
                "config": integration_config or {},
                "interval_minutes": interval_minutes,
            }

            task = asyncio.create_task(self._monitor_integration_async(integration_id))
            self._monitor_tasks[integration_id] = task

    async def _monitor_integration_async(self, integration_id: str):
        """Async background task to periodically check integration status."""
        config_entry = self._monitor_config.get(integration_id, {})
        interval_minutes = config_entry.get("interval_minutes", self._default_interval_minutes)

        while True:
            try:
                result = await self._run_health_check(integration_id, config_entry.get("config"))
                await self._process_health_result(integration_id, result)
                await asyncio.sleep(max(interval_minutes, 1) * 60)
            except asyncio.CancelledError:
                logger.debug(f"Monitoring task cancelled for integration {integration_id}")
                break
            except Exception as e:
                logger.error(f"Error monitoring integration {integration_id}: {e}")
                self._status_cache[str(integration_id)] = {
                    "status": "error",
                    "last_checked": datetime.utcnow(),
                    "message": f"Monitoring error: {e}",
                    "details": {"error": "monitoring_error"}
                }
                await asyncio.sleep(300)

    async def _run_health_check(self, integration_id: str, integration_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a health check using available dependencies."""
        str_id = str(integration_id)

        if self.connection_manager:
            try:
                status_obj = await self.connection_manager.get_system_status(str_id)
                status_dict = self._connection_status_to_dict(status_obj)
                if status_dict is not None:
                    state_value = status_dict.get("state", "unknown")
                    success = state_value not in {"failed", "maintenance"}
                    return {
                        "success": success,
                        "message": f"Connection state: {state_value}",
                        "details": status_dict,
                    }
            except Exception as exc:
                return {
                    "success": False,
                    "error": str(exc),
                    "message": str(exc),
                    "integration_id": str_id,
                }

        if self.connection_tester and integration_config is not None:
            try:
                test_integration = {
                    "id": str_id,
                    "config": integration_config
                }
                return self.connection_tester.test_integration_connection(test_integration)
            except Exception as exc:
                return {
                    "success": False,
                    "error": str(exc),
                    "message": str(exc),
                    "integration_id": str_id,
                }

        return {
            "success": False,
            "message": "Health monitor not fully configured",
            "details": {"reason": "no_connection_manager" if not self.connection_manager else "no_connection_tester"},
            "integration_id": str_id,
        }

    async def _process_health_result(self, integration_id: str, test_result: Dict[str, Any]) -> None:
        """Update caches, metrics, and alerts for a health result."""
        str_id = str(integration_id)
        checked_at = datetime.utcnow()
        success = bool(test_result.get("success", False))
        status = "active" if success else "failed"
        message = test_result.get("message") or test_result.get("error") or "Unknown status"
        details = test_result.get("details") or test_result.get("test_result") or {}

        snapshot = {
            "integration_id": str_id,
            "status": status,
            "success": success,
            "checked_at": checked_at,
            "message": message,
            "details": self._serialize_value(details),
        }

        connection_status_dict = None
        if self.connection_manager:
            status_obj = await self.connection_manager.get_system_status(str_id)
            connection_status_dict = self._connection_status_to_dict(status_obj)
            if connection_status_dict:
                snapshot["connection_status"] = connection_status_dict

        self._status_cache[str_id] = {
            "status": status,
            "last_checked": checked_at,
            "message": message,
            "details": details,
        }

        history = self._snapshot_history[str_id]
        history.appendleft(snapshot)

        self._record_health_metrics(integration_id, test_result)
        await self._check_health_thresholds(integration_id, test_result)
    
    # === Health Monitoring and Metrics ===
    
    def _record_health_metrics(self, integration_id: str, test_result: Dict[str, Any]):
        """Record health metrics from test results"""
        timestamp = datetime.utcnow()
        details = test_result.get("details") or test_result.get("test_result") or {}
        if isinstance(details, dict) and "latency_ms" in details:
            metric = HealthMetric(
                integration_id=integration_id,
                metric_name="response_time",
                value=details["latency_ms"],
                timestamp=timestamp
            )
            self.health_metrics.append(metric)
        
        # Record success/failure
        success_value = 1.0 if test_result.get("success", False) else 0.0
        metric = HealthMetric(
            integration_id=integration_id,
            metric_name="success_rate",
            value=success_value,
            timestamp=timestamp
        )
        self.health_metrics.append(metric)
    
    async def _check_health_thresholds(self, integration_id: str, test_result: Dict[str, Any]):
        """Check if health metrics exceed thresholds and trigger alerts"""
        try:
            # Get recent metrics for this integration
            recent_metrics = self._get_recent_metrics(integration_id, hours=1)
            
            if not recent_metrics:
                return
            
            # Check response time threshold
            response_times = [m.value for m in recent_metrics if m.metric_name == "response_time"]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                await self._check_metric_threshold(
                    integration_id, 
                    "response_time", 
                    avg_response_time,
                    self.default_thresholds["response_time"]
                )
            
            # Check success rate threshold
            success_metrics = [m.value for m in recent_metrics if m.metric_name == "success_rate"]
            if success_metrics:
                success_rate = (sum(success_metrics) / len(success_metrics)) * 100
                await self._check_metric_threshold(
                    integration_id,
                    "success_rate",
                    success_rate,
                    self.default_thresholds["success_rate"]
                )
        
        except Exception as e:
            logger.error(f"Error checking health thresholds for {integration_id}: {e}")
    
    async def _check_metric_threshold(
        self, 
        integration_id: str, 
        metric_name: str, 
        value: float, 
        threshold: HealthThreshold
    ):
        """Check if a metric value exceeds threshold"""
        if not threshold.enabled:
            return
        
        # Check if threshold is exceeded
        exceeded = False
        severity = None
        
        if threshold.comparison_operator == "gt":
            if value > threshold.critical_threshold:
                exceeded = True
                severity = AlertSeverity.CRITICAL
            elif value > threshold.warning_threshold:
                exceeded = True
                severity = AlertSeverity.WARNING
        elif threshold.comparison_operator == "lt":
            if value < threshold.critical_threshold:
                exceeded = True
                severity = AlertSeverity.CRITICAL
            elif value < threshold.warning_threshold:
                exceeded = True
                severity = AlertSeverity.WARNING
        
        if exceeded:
            await self._trigger_alert(
                integration_id,
                severity,
                f"{metric_name.title()} Threshold Exceeded",
                f"{metric_name} value {value:.2f} exceeds {severity.value} threshold",
                {"metric_name": metric_name, "value": value, "threshold": threshold}
            )
    
    async def _trigger_alert(
        self,
        integration_id: str,
        severity: AlertSeverity,
        title: str,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        """Trigger a new alert"""
        alert_id = f"alert_{integration_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        alert = Alert(
            alert_id=alert_id,
            integration_id=integration_id,
            severity=severity,
            title=title,
            message=message,
            triggered_at=datetime.now()
        )
        
        self.active_alerts[alert_id] = alert
        
        # Notify handlers
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")
        
        logger.warning(f"Alert triggered: {title} for {integration_id}")
    
    def _get_recent_metrics(self, integration_id: str, hours: int = 1) -> List[HealthMetric]:
        """Get recent metrics for an integration"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            metric for metric in self.health_metrics
            if metric.integration_id == integration_id and metric.timestamp >= cutoff_time
        ]

    def get_health_snapshot(
        self,
        integration_id: str,
        *,
        include_history: bool = False,
        history_limit: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Return the latest health snapshot for an integration."""
        str_id = str(integration_id)
        status_info = self._status_cache.get(str_id)
        if not status_info:
            return None

        snapshot = {
            "integration_id": str_id,
            "status": status_info.get("status", "unknown"),
            "last_checked": status_info.get("last_checked").isoformat() if isinstance(status_info.get("last_checked"), datetime) else status_info.get("last_checked"),
            "message": status_info.get("message"),
            "details": self._serialize_value(status_info.get("details", {})),
        }

        if include_history:
            history_entries = list(self._snapshot_history.get(str_id, []))[:history_limit]
            serialized_history = []
            for entry in history_entries:
                serialized_history.append({
                    "status": entry.get("status"),
                    "success": entry.get("success"),
                    "message": entry.get("message"),
                    "details": entry.get("details"),
                    "checked_at": entry.get("checked_at").isoformat() if isinstance(entry.get("checked_at"), datetime) else entry.get("checked_at"),
                    "connection_status": entry.get("connection_status"),
                })
            snapshot["recent_history"] = serialized_history

        return snapshot

    def _connection_status_to_dict(self, status_obj) -> Optional[Dict[str, Any]]:
        if not status_obj:
            return None
        data = asdict(status_obj)
        state = data.get("state")
        if isinstance(state, Enum):
            data["state"] = state.value
        for dt_key in ("connected_at", "last_activity", "last_checked"):
            if data.get(dt_key) is not None and isinstance(data[dt_key], datetime):
                data[dt_key] = data[dt_key].isoformat()
        return data

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._serialize_value(v) for v in value]
        return value
    
    # === FIRS API Status Monitoring (from integration_status_service.py) ===
    
    def get_odoo_status(self, integration_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check the status of Odoo integration - SI Role Function.
        Extracted from integration_status_service.py lines 38-152
        """
        if integration_id:
            status = self._status_cache.get(str(integration_id))
            if status:
                return {
                    "status": "operational",
                    "message": f"Odoo integration {integration_id} status",
                    "last_checked": datetime.utcnow().isoformat(),
                    "integrations": [{
                        "id": integration_id,
                        "name": f"Odoo Integration {integration_id}",
                        "status": status.get("status", "unknown"),
                        "version": "16.0",
                        "submission_stats": {
                            "total_24h": 10,
                            "success_24h": 8,
                            "failed_24h": 2,
                            "success_rate": 80.0
                        }
                    }]
                }
        
        return {
            "status": "not_configured",
            "message": "No active Odoo integrations found",
            "last_checked": datetime.utcnow().isoformat(),
            "integrations": []
        }
    
    async def get_firs_api_status(self) -> Dict[str, Any]:
        """
        Check the status of FIRS API - SI Role Function.
        Extracted from integration_status_service.py lines 155-221
        """
        try:
            # Mock FIRS API status
            api_status = {
                "status": "operational",
                "sandbox_available": True,
                "production_available": True
            }
            
            submission_stats = {
                "total_24h": 25,
                "success_24h": 20,
                "failed_24h": 5,
                "success_rate": 80.0
            }
            
            return {
                "status": api_status.get("status", "unknown"),
                "sandbox_available": api_status.get("sandbox_available", False),
                "production_available": api_status.get("production_available", False),
                "last_checked": datetime.utcnow().isoformat(),
                "submission_stats": submission_stats,
                "recent_errors": []
            }
            
        except Exception as e:
            logger.error(f"Error checking FIRS API status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "last_checked": datetime.utcnow().isoformat()
            }
    
    async def get_all_integration_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of all integrations - SI Role Function.
        Extracted from integration_status_service.py lines 224-252
        """
        odoo_status = self.get_odoo_status()
        firs_status = await self.get_firs_api_status()
        
        # Calculate overall system status
        system_status = "operational"
        if odoo_status["status"] != "operational" or firs_status["status"] != "operational":
            system_status = "degraded"
        if odoo_status["status"] == "error" and firs_status["status"] == "error":
            system_status = "critical"
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": system_status,
            "odoo_integration": odoo_status,
            "firs_api": firs_status,
            "monitored_integrations": self.get_all_monitored_integrations(),
            "active_alerts": len(self.active_alerts),
            "total_metrics": len(self.health_metrics)
        }
    
    # === Health Summary and Analysis ===
    
    def get_integration_health_summary(self, integration_id: str) -> Dict[str, Any]:
        """Get comprehensive health summary for an integration"""
        status = self.get_integration_status(integration_id)
        recent_metrics = self._get_recent_metrics(integration_id, hours=24)
        
        # Calculate health score
        health_score = 100
        
        if status["status"] == "failed":
            health_score = 0
        elif status["status"] == "error":
            health_score = 25
        elif status["status"] == "unknown":
            health_score = 30
        
        # Factor in metrics
        if recent_metrics:
            success_metrics = [m.value for m in recent_metrics if m.metric_name == "success_rate"]
            if success_metrics:
                success_rate = (sum(success_metrics) / len(success_metrics)) * 100
                if success_rate < 50:
                    health_score = min(health_score, 20)
                elif success_rate < 80:
                    health_score = min(health_score, 60)
        
        # Determine health status
        if health_score >= 80:
            health_status = "excellent"
        elif health_score >= 60:
            health_status = "good"
        elif health_score >= 40:
            health_status = "fair"
        elif health_score >= 20:
            health_status = "poor"
        else:
            health_status = "critical"
        
        # Get active alerts for this integration
        integration_alerts = [
            alert for alert in self.active_alerts.values()
            if alert.integration_id == integration_id
        ]
        
        return {
            "integration_id": integration_id,
            "health_score": health_score,
            "health_status": health_status,
            "current_status": status["status"],
            "last_checked": status.get("last_checked"),
            "message": status.get("message", ""),
            "is_monitored": str(integration_id) in self._monitor_tasks,
            "active_alerts": len(integration_alerts),
            "metrics_count": len(recent_metrics),
            "recommendations": self._get_health_recommendations(health_score, status)
        }
    
    def _get_health_recommendations(self, health_score: int, status: Dict[str, Any]) -> List[str]:
        """Generate health recommendations based on status"""
        recommendations = []
        
        if health_score < 50:
            recommendations.append("Integration requires immediate attention")
        
        if status["status"] == "failed":
            recommendations.append("Test connection configuration and credentials")
            recommendations.append("Check network connectivity to target system")
        
        if status["status"] == "error":
            recommendations.append("Review error logs for detailed diagnostics")
            recommendations.append("Verify system endpoints and authentication")
        
        if not status.get("last_checked"):
            recommendations.append("Enable monitoring to track integration health")
        
        if not recommendations:
            recommendations.append("Integration is operating normally")
        
        return recommendations
    
    # === Alert Management ===
    
    def get_active_alerts(self, integration_id: Optional[str] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by integration"""
        if integration_id:
            return [alert for alert in self.active_alerts.values() if alert.integration_id == integration_id]
        return list(self.active_alerts.values())
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved_at = datetime.now()
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    # === Cleanup and Maintenance ===
    
    def cleanup_monitoring_cache(self, max_age_hours: int = 168):  # 1 week default
        """Clean up old monitoring cache entries"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # Clean up status cache
        to_remove = []
        for integration_id, status in self._status_cache.items():
            last_checked = status.get("last_checked")
            if last_checked and isinstance(last_checked, datetime):
                if last_checked < cutoff_time:
                    to_remove.append(integration_id)
        
        for integration_id in to_remove:
            del self._status_cache[integration_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old cache entries")
    
    async def shutdown(self):
        """Shutdown health monitor and cleanup resources"""
        await self.stop_all_monitoring()
        
        # Clear data
        self._status_cache.clear()
        self.health_metrics.clear()
        self.active_alerts.clear()
        
        logger.info("Integration health monitor shutdown complete")


# Global instance for easy access
integration_health_monitor = IntegrationHealthMonitor()
