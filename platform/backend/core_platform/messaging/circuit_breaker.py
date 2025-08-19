"""
TaxPoynt Platform - Circuit Breaker Pattern Implementation
========================================================
Production-grade circuit breaker for service failure protection.
Prevents cascade failures and provides graceful degradation.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Failures detected, blocking requests
    HALF_OPEN = "half_open" # Testing if service has recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5           # Failures before opening circuit
    recovery_timeout: int = 60           # Seconds before attempting recovery
    success_threshold: int = 3           # Successes needed to close circuit
    timeout_seconds: float = 30.0        # Request timeout
    rolling_window_seconds: int = 60     # Failure tracking window
    max_concurrent_requests: int = 10    # Max requests in HALF_OPEN state


@dataclass
class CircuitBreakerMetrics:
    """Circuit breaker metrics tracking"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeouts: int = 0
    circuit_opened_count: int = 0
    circuit_closed_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    current_state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    failure_history: List[datetime] = field(default_factory=list)


class CircuitBreakerException(Exception):
    """Circuit breaker specific exception"""
    def __init__(self, message: str, state: CircuitState):
        super().__init__(message)
        self.state = state


class CircuitBreaker:
    """
    Circuit Breaker implementation for service protection
    
    Features:
    - Automatic failure detection and circuit opening
    - Configurable thresholds and timeouts
    - Rolling window failure tracking
    - Graceful recovery testing
    - Detailed metrics and monitoring
    - Redis-backed state persistence
    """
    
    def __init__(self, 
                 name: str,
                 config: CircuitBreakerConfig,
                 redis_client: Optional[redis.Redis] = None):
        """Initialize circuit breaker"""
        self.name = name
        self.config = config
        self.redis = redis_client
        
        # State management
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self.half_open_requests = 0
        
        # Metrics
        self.metrics = CircuitBreakerMetrics()
        
        # Redis keys for persistence
        if self.redis:
            self.state_key = f"taxpoynt:circuit_breaker:{name}:state"
            self.metrics_key = f"taxpoynt:circuit_breaker:{name}:metrics"
            self.failures_key = f"taxpoynt:circuit_breaker:{name}:failures"
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        # Check if circuit allows request
        if not await self._should_allow_request():
            self.metrics.total_requests += 1
            await self._update_metrics()
            raise CircuitBreakerException(
                f"Circuit breaker '{self.name}' is {self.state.value}",
                self.state
            )
        
        # Track request
        self.metrics.total_requests += 1
        start_time = time.time()
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.timeout_seconds
            )
            
            # Record success
            await self._record_success()
            return result
            
        except asyncio.TimeoutError:
            # Record timeout
            self.metrics.timeouts += 1
            await self._record_failure()
            raise CircuitBreakerException(
                f"Request to '{self.name}' timed out after {self.config.timeout_seconds}s",
                self.state
            )
            
        except Exception as e:
            # Record failure
            await self._record_failure()
            raise e
        
        finally:
            await self._update_metrics()
    
    async def _should_allow_request(self) -> bool:
        """Check if request should be allowed based on circuit state"""
        await self._load_state_from_redis()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                time_since_failure = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
                if time_since_failure >= self.config.recovery_timeout:
                    await self._transition_to_half_open()
                    return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # Allow limited requests for testing
            if self.half_open_requests < self.config.max_concurrent_requests:
                self.half_open_requests += 1
                return True
            return False
        
        return False
    
    async def _record_success(self):
        """Record successful request"""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = datetime.now(timezone.utc)
        
        # Check if we should close the circuit
        if self.state == CircuitState.HALF_OPEN:
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                await self._transition_to_closed()
    
    async def _record_failure(self):
        """Record failed request"""
        now = datetime.now(timezone.utc)
        
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = now
        self.last_failure_time = now
        
        # Add to failure history
        self.metrics.failure_history.append(now)
        
        # Clean old failures from rolling window
        cutoff_time = now - timedelta(seconds=self.config.rolling_window_seconds)
        self.metrics.failure_history = [
            failure_time for failure_time in self.metrics.failure_history
            if failure_time > cutoff_time
        ]
        
        # Store failures in Redis
        if self.redis:
            await self._store_failures_in_redis()
        
        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED:
            if len(self.metrics.failure_history) >= self.config.failure_threshold:
                await self._transition_to_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state returns to open
            await self._transition_to_open()
    
    async def _transition_to_open(self):
        """Transition circuit to OPEN state"""
        self.state = CircuitState.OPEN
        self.metrics.current_state = CircuitState.OPEN
        self.metrics.circuit_opened_count += 1
        self.half_open_requests = 0
        
        await self._persist_state()
        
        logger.warning(f"Circuit breaker '{self.name}' opened after {self.metrics.consecutive_failures} failures")
    
    async def _transition_to_half_open(self):
        """Transition circuit to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.metrics.current_state = CircuitState.HALF_OPEN
        self.half_open_requests = 0
        
        await self._persist_state()
        
        logger.info(f"Circuit breaker '{self.name}' attempting recovery (HALF_OPEN)")
    
    async def _transition_to_closed(self):
        """Transition circuit to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.metrics.current_state = CircuitState.CLOSED
        self.metrics.circuit_closed_count += 1
        self.half_open_requests = 0
        
        await self._persist_state()
        
        logger.info(f"Circuit breaker '{self.name}' closed after {self.metrics.consecutive_successes} successes")
    
    async def _persist_state(self):
        """Persist circuit breaker state to Redis"""
        if not self.redis:
            return
        
        try:
            state_data = {
                "state": self.state.value,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "half_open_requests": self.half_open_requests,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.redis.hset(self.state_key, mapping=state_data)
            await self.redis.expire(self.state_key, 3600)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Failed to persist circuit breaker state: {e}")
    
    async def _load_state_from_redis(self):
        """Load circuit breaker state from Redis"""
        if not self.redis:
            return
        
        try:
            state_data = await self.redis.hgetall(self.state_key)
            
            if state_data:
                self.state = CircuitState(state_data.get("state", CircuitState.CLOSED.value))
                self.half_open_requests = int(state_data.get("half_open_requests", 0))
                self.metrics.consecutive_failures = int(state_data.get("consecutive_failures", 0))
                self.metrics.consecutive_successes = int(state_data.get("consecutive_successes", 0))
                
                if state_data.get("last_failure_time"):
                    self.last_failure_time = datetime.fromisoformat(state_data["last_failure_time"])
                    self.metrics.last_failure_time = self.last_failure_time
            
        except Exception as e:
            logger.error(f"Failed to load circuit breaker state: {e}")
    
    async def _store_failures_in_redis(self):
        """Store failure history in Redis"""
        if not self.redis:
            return
        
        try:
            # Store recent failures with TTL
            for failure_time in self.metrics.failure_history:
                timestamp = int(failure_time.timestamp())
                await self.redis.zadd(self.failures_key, {str(timestamp): timestamp})
            
            # Remove old failures
            cutoff_timestamp = int((datetime.now(timezone.utc) - 
                                  timedelta(seconds=self.config.rolling_window_seconds)).timestamp())
            await self.redis.zremrangebyscore(self.failures_key, 0, cutoff_timestamp)
            
            # Set TTL
            await self.redis.expire(self.failures_key, self.config.rolling_window_seconds * 2)
            
        except Exception as e:
            logger.error(f"Failed to store failures in Redis: {e}")
    
    async def _update_metrics(self):
        """Update metrics in Redis"""
        if not self.redis:
            return
        
        try:
            metrics_data = {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "timeouts": self.metrics.timeouts,
                "circuit_opened_count": self.metrics.circuit_opened_count,
                "circuit_closed_count": self.metrics.circuit_closed_count,
                "current_state": self.metrics.current_state.value,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "failure_count_in_window": len(self.metrics.failure_history),
                "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.redis.hset(self.metrics_key, mapping=metrics_data)
            await self.redis.expire(self.metrics_key, 3600)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        await self._load_state_from_redis()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
                "rolling_window_seconds": self.config.rolling_window_seconds
            },
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": (
                    self.metrics.successful_requests / max(self.metrics.total_requests, 1)
                ) * 100,
                "timeouts": self.metrics.timeouts,
                "circuit_opened_count": self.metrics.circuit_opened_count,
                "circuit_closed_count": self.metrics.circuit_closed_count,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "failures_in_window": len(self.metrics.failure_history),
                "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None
            },
            "health": {
                "is_healthy": self.state == CircuitState.CLOSED,
                "time_until_retry": self._time_until_retry() if self.state == CircuitState.OPEN else 0
            }
        }
    
    def _time_until_retry(self) -> int:
        """Calculate seconds until next retry attempt"""
        if self.state != CircuitState.OPEN or not self.last_failure_time:
            return 0
        
        elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
        return max(0, int(self.config.recovery_timeout - elapsed))
    
    async def reset(self):
        """Manually reset circuit breaker to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.half_open_requests = 0
        self.last_failure_time = None
        
        await self._persist_state()
        await self._update_metrics()
        
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, 
                          name: str, 
                          config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.circuit_breakers:
            config = config or CircuitBreakerConfig()
            self.circuit_breakers[name] = CircuitBreaker(name, config, self.redis)
        
        return self.circuit_breakers[name]
    
    async def get_all_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers"""
        status = {}
        for name, cb in self.circuit_breakers.items():
            status[name] = await cb.get_status()
        
        return {
            "circuit_breakers": status,
            "total_count": len(self.circuit_breakers),
            "healthy_count": len([cb for cb in status.values() if cb["health"]["is_healthy"]]),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self.circuit_breakers.values():
            await cb.reset()


# Global circuit breaker manager
_circuit_breaker_manager: Optional[CircuitBreakerManager] = None


def get_circuit_breaker_manager(redis_client: Optional[redis.Redis] = None) -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    global _circuit_breaker_manager
    if _circuit_breaker_manager is None:
        _circuit_breaker_manager = CircuitBreakerManager(redis_client)
    return _circuit_breaker_manager


def circuit_breaker(name: str, 
                   config: Optional[CircuitBreakerConfig] = None,
                   redis_client: Optional[redis.Redis] = None):
    """Decorator for circuit breaker protection"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            manager = get_circuit_breaker_manager(redis_client)
            cb = manager.get_circuit_breaker(name, config)
            return await cb.call(func, *args, **kwargs)
        return wrapper
    return decorator