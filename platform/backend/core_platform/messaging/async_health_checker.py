"""
TaxPoynt Platform - Async Health Checker
=======================================
Non-blocking health check system for production services.
Prevents blocking the main event loop with health monitoring.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
import aiohttp

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckConfig:
    """Health check configuration"""
    check_interval: int = 30        # Seconds between checks
    timeout: float = 10.0           # Request timeout
    retries: int = 3                # Retry attempts
    retry_delay: float = 1.0        # Delay between retries
    degraded_threshold: float = 5.0 # Response time threshold for degraded
    unhealthy_threshold: int = 3    # Failed checks before unhealthy


@dataclass
class HealthMetrics:
    """Health metrics for a service"""
    service_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    response_time_ms: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    uptime_percentage: float = 100.0
    error_message: Optional[str] = None
    check_history: List[Dict[str, Any]] = field(default_factory=list)


class ServiceHealthChecker:
    """Individual service health checker"""
    
    def __init__(self, 
                 service_name: str,
                 check_function: Callable,
                 config: HealthCheckConfig):
        self.service_name = service_name
        self.check_function = check_function
        self.config = config
        self.metrics = HealthMetrics(service_name)
        self._check_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"Health checker initialized for {service_name}")
    
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        if self._running:
            return
        
        self._running = True
        self._check_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started health monitoring for {self.service_name}")
    
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped health monitoring for {self.service_name}")
    
    async def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self._running:
            try:
                await self.perform_health_check()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error for {self.service_name}: {e}")
                await asyncio.sleep(self.config.check_interval)
    
    async def perform_health_check(self) -> HealthMetrics:
        """Perform single health check"""
        start_time = time.time()
        check_time = datetime.now(timezone.utc)
        
        try:
            # Perform health check with retries
            result = await self._execute_check_with_retries()
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Update metrics
            await self._update_success_metrics(check_time, response_time, result)
            
        except Exception as e:
            # Update failure metrics
            await self._update_failure_metrics(check_time, str(e))
        
        # Update status based on metrics
        self._update_health_status()
        
        # Trim history to last 100 entries
        if len(self.metrics.check_history) > 100:
            self.metrics.check_history = self.metrics.check_history[-100:]
        
        return self.metrics
    
    async def _execute_check_with_retries(self) -> Any:
        """Execute health check with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.check_function(),
                    timeout=self.config.timeout
                )
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self.config.retries:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                raise e
                
            except Exception as e:
                last_exception = e
                if attempt < self.config.retries:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                raise e
        
        raise last_exception
    
    async def _update_success_metrics(self, check_time: datetime, response_time: float, result: Any):
        """Update metrics after successful check"""
        self.metrics.last_check_time = check_time
        self.metrics.last_success_time = check_time
        self.metrics.response_time_ms = response_time
        self.metrics.success_count += 1
        self.metrics.consecutive_failures = 0
        self.metrics.error_message = None
        
        # Add to history
        self.metrics.check_history.append({
            "timestamp": check_time.isoformat(),
            "status": "success",
            "response_time_ms": response_time,
            "result": str(result)[:200] if result else None  # Truncate large results
        })
        
        logger.debug(f"Health check passed for {self.service_name} ({response_time:.1f}ms)")
    
    async def _update_failure_metrics(self, check_time: datetime, error_message: str):
        """Update metrics after failed check"""
        self.metrics.last_check_time = check_time
        self.metrics.last_failure_time = check_time
        self.metrics.failure_count += 1
        self.metrics.consecutive_failures += 1
        self.metrics.error_message = error_message
        
        # Add to history
        self.metrics.check_history.append({
            "timestamp": check_time.isoformat(),
            "status": "failure",
            "error": error_message[:200]  # Truncate long errors
        })
        
        logger.warning(f"Health check failed for {self.service_name}: {error_message}")
    
    def _update_health_status(self):
        """Update overall health status"""
        if self.metrics.consecutive_failures >= self.config.unhealthy_threshold:
            self.metrics.status = HealthStatus.UNHEALTHY
        elif self.metrics.response_time_ms > self.config.degraded_threshold * 1000:
            self.metrics.status = HealthStatus.DEGRADED
        elif self.metrics.consecutive_failures > 0:
            self.metrics.status = HealthStatus.DEGRADED
        else:
            self.metrics.status = HealthStatus.HEALTHY
        
        # Calculate uptime percentage
        total_checks = self.metrics.success_count + self.metrics.failure_count
        if total_checks > 0:
            self.metrics.uptime_percentage = (self.metrics.success_count / total_checks) * 100


class AsyncHealthCheckManager:
    """
    Manages async health checks for multiple services
    
    Features:
    - Non-blocking health monitoring
    - Configurable check intervals and timeouts
    - Health status aggregation
    - Redis-backed status persistence
    - Real-time health status API
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.health_checkers: Dict[str, ServiceHealthChecker] = {}
        self._aggregation_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Redis keys
        if self.redis:
            self.health_key = "taxpoynt:health_status"
            self.metrics_key = "taxpoynt:health_metrics"
        
        logger.info("Async Health Check Manager initialized")
    
    def register_service(self, 
                        service_name: str,
                        check_function: Callable,
                        config: Optional[HealthCheckConfig] = None):
        """Register a service for health monitoring"""
        config = config or HealthCheckConfig()
        
        checker = ServiceHealthChecker(service_name, check_function, config)
        self.health_checkers[service_name] = checker
        
        logger.info(f"Registered health check for service: {service_name}")
    
    async def start_all_monitoring(self):
        """Start monitoring all registered services"""
        if self._running:
            return
        
        self._running = True
        
        # Start individual service monitoring
        for checker in self.health_checkers.values():
            await checker.start_monitoring()
        
        # Start aggregation task
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())
        
        logger.info(f"Started health monitoring for {len(self.health_checkers)} services")
    
    async def stop_all_monitoring(self):
        """Stop all health monitoring"""
        self._running = False
        
        # Stop aggregation task
        if self._aggregation_task:
            self._aggregation_task.cancel()
            try:
                await self._aggregation_task
            except asyncio.CancelledError:
                pass
        
        # Stop individual service monitoring
        for checker in self.health_checkers.values():
            await checker.stop_monitoring()
        
        logger.info("Stopped all health monitoring")
    
    async def _aggregation_loop(self):
        """Aggregate health status and persist to Redis"""
        while self._running:
            try:
                await self._aggregate_and_persist_health_status()
                await asyncio.sleep(10)  # Aggregate every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health aggregation error: {e}")
                await asyncio.sleep(10)
    
    async def _aggregate_and_persist_health_status(self):
        """Aggregate health status across all services"""
        if not self.redis:
            return
        
        try:
            overall_status = HealthStatus.HEALTHY
            healthy_count = 0
            total_count = len(self.health_checkers)
            
            service_statuses = {}
            
            for service_name, checker in self.health_checkers.items():
                metrics = checker.metrics
                service_statuses[service_name] = {
                    "status": metrics.status.value,
                    "last_check": metrics.last_check_time.isoformat() if metrics.last_check_time else None,
                    "response_time_ms": metrics.response_time_ms,
                    "uptime_percentage": metrics.uptime_percentage,
                    "consecutive_failures": metrics.consecutive_failures,
                    "error_message": metrics.error_message
                }
                
                if metrics.status == HealthStatus.HEALTHY:
                    healthy_count += 1
                elif metrics.status == HealthStatus.UNHEALTHY and overall_status != HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.UNHEALTHY
                elif metrics.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            
            # Determine overall system status
            if healthy_count == 0:
                overall_status = HealthStatus.UNHEALTHY
            elif healthy_count < total_count:
                if overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
            
            # Aggregate health data
            health_data = {
                "overall_status": overall_status.value,
                "healthy_services": healthy_count,
                "total_services": total_count,
                "health_percentage": (healthy_count / max(total_count, 1)) * 100,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "services": service_statuses
            }
            
            # Store in Redis
            await self.redis.hset(self.health_key, mapping={
                k: str(v) if not isinstance(v, dict) else str(v) 
                for k, v in health_data.items()
            })
            await self.redis.expire(self.health_key, 300)  # 5 min TTL
            
            # Store detailed metrics
            for service_name, checker in self.health_checkers.items():
                metrics_data = {
                    "service_name": service_name,
                    "status": checker.metrics.status.value,
                    "success_count": checker.metrics.success_count,
                    "failure_count": checker.metrics.failure_count,
                    "consecutive_failures": checker.metrics.consecutive_failures,
                    "response_time_ms": checker.metrics.response_time_ms,
                    "uptime_percentage": checker.metrics.uptime_percentage,
                    "last_success": checker.metrics.last_success_time.isoformat() if checker.metrics.last_success_time else None,
                    "last_failure": checker.metrics.last_failure_time.isoformat() if checker.metrics.last_failure_time else None,
                    "error_message": checker.metrics.error_message or "",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                await self.redis.hset(f"{self.metrics_key}:{service_name}", mapping=metrics_data)
                await self.redis.expire(f"{self.metrics_key}:{service_name}", 3600)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Failed to aggregate health status: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        service_health = {}
        overall_status = HealthStatus.HEALTHY
        healthy_count = 0
        
        for service_name, checker in self.health_checkers.items():
            metrics = checker.metrics
            service_health[service_name] = {
                "status": metrics.status.value,
                "last_check_time": metrics.last_check_time.isoformat() if metrics.last_check_time else None,
                "last_success_time": metrics.last_success_time.isoformat() if metrics.last_success_time else None,
                "last_failure_time": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
                "response_time_ms": metrics.response_time_ms,
                "success_count": metrics.success_count,
                "failure_count": metrics.failure_count,
                "consecutive_failures": metrics.consecutive_failures,
                "uptime_percentage": metrics.uptime_percentage,
                "error_message": metrics.error_message
            }
            
            if metrics.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif metrics.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif metrics.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        # Calculate overall health
        total_services = len(self.health_checkers)
        health_percentage = (healthy_count / max(total_services, 1)) * 100
        
        return {
            "overall_status": overall_status.value,
            "health_percentage": health_percentage,
            "healthy_services": healthy_count,
            "total_services": total_services,
            "services": service_health,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_service_now(self, service_name: str) -> Optional[HealthMetrics]:
        """Force immediate health check for a specific service"""
        if service_name not in self.health_checkers:
            return None
        
        checker = self.health_checkers[service_name]
        return await checker.perform_health_check()
    
    async def reset_service_metrics(self, service_name: str) -> bool:
        """Reset metrics for a specific service"""
        if service_name not in self.health_checkers:
            return False
        
        checker = self.health_checkers[service_name]
        checker.metrics = HealthMetrics(service_name)
        
        logger.info(f"Reset metrics for service: {service_name}")
        return True


# Global health check manager
_health_check_manager: Optional[AsyncHealthCheckManager] = None


def get_health_check_manager(redis_client: Optional[redis.Redis] = None) -> AsyncHealthCheckManager:
    """Get global health check manager"""
    global _health_check_manager
    if _health_check_manager is None:
        _health_check_manager = AsyncHealthCheckManager(redis_client)
    return _health_check_manager


async def setup_default_health_checks(manager: AsyncHealthCheckManager):
    """Setup default health checks for core services"""
    
    # Redis health check
    async def check_redis():
        if manager.redis:
            await manager.redis.ping()
            return "Redis connection healthy"
        return "Redis not configured"
    
    manager.register_service("redis", check_redis, HealthCheckConfig(
        check_interval=30,
        timeout=5.0,
        unhealthy_threshold=3
    ))
    
    # Database health check
    async def check_database():
        try:
            from core_platform.data_management.connection_pool import get_connection_pool
            pool = get_connection_pool()
            async with pool.get_session() as session:
                result = await session.execute("SELECT 1")
                return "Database connection healthy"
        except Exception as e:
            raise Exception(f"Database check failed: {e}")
    
    manager.register_service("database", check_database, HealthCheckConfig(
        check_interval=30,
        timeout=10.0,
        unhealthy_threshold=2
    ))
    
    # Message router health check  
    async def check_message_router():
        try:
            from core_platform.messaging.redis_message_router import get_redis_message_router
            router = get_redis_message_router(manager.redis)
            stats = await router.get_routing_statistics()
            return f"Message router healthy - {stats.get('cluster_wide', {}).get('active_instances', 0)} instances"
        except Exception as e:
            raise Exception(f"Message router check failed: {e}")
    
    manager.register_service("message_router", check_message_router, HealthCheckConfig(
        check_interval=60,
        timeout=15.0,
        unhealthy_threshold=2
    ))
    
    logger.info("Default health checks configured")