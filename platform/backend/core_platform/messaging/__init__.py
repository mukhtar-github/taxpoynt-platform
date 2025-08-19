"""
Core Platform Messaging Package
Event-driven communication infrastructure for TaxPoynt Platform
"""

# Event Bus Components
from .event_bus import (
    EventBus,
    Event,
    EventPriority,
    EventScope,
    EventStatus,
    get_event_bus,
    initialize_event_bus,
    shutdown_event_bus
)

# Message Router Components
from .message_router import (
    MessageRouter,
    ServiceRole,
    RoutingStrategy,
    MessageType,
    RoutingRule,
    ServiceEndpoint,
    RoutingContext,
    RoutedMessage,
    get_message_router,
    initialize_message_router
)

# Queue Manager Components
from .queue_manager import (
    QueueManager,
    MessageQueue,
    QueueType,
    QueueStrategy,
    MessageStatus,
    QueuedMessage,
    QueueConfiguration,
    QueueMetrics,
    get_queue_manager,
    initialize_queue_manager
)

# Pub-Sub Coordinator Components
from .pub_sub_coordinator import (
    PubSubCoordinator,
    Topic,
    Subscription,
    Publication,
    SubscriptionType,
    DeliveryMode,
    TopicType,
    DeliveryReceipt,
    get_pubsub_coordinator,
    initialize_pubsub_coordinator
)

# Dead Letter Handler Components
from .dead_letter_handler import (
    DeadLetterHandler,
    DeadLetterMessage,
    FailureContext,
    FailureReason,
    RecoveryAction,
    RecoveryPlan,
    DeadLetterStats,
    AlertLevel,
    get_dead_letter_handler,
    initialize_dead_letter_handler
)

# Redis Message Router Components (Phase 3)
from .redis_message_router import (
    RedisMessageRouter,
    get_redis_message_router
)

# Horizontal Scaling Coordinator Components (Phase 3)
from .horizontal_scaling_coordinator import (
    HorizontalScalingCoordinator,
    ScalingPolicy,
    InstanceMetrics,
    ScalingConfiguration,
    get_horizontal_scaling_coordinator
)

# Circuit Breaker Components (Phase 3)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerMetrics,
    CircuitBreakerException,
    CircuitBreakerManager,
    CircuitState,
    get_circuit_breaker_manager,
    circuit_breaker
)

# Async Health Checker Components (Phase 3)
from .async_health_checker import (
    AsyncHealthCheckManager,
    ServiceHealthChecker,
    HealthCheckConfig,
    HealthMetrics,
    HealthStatus,
    get_health_check_manager,
    setup_default_health_checks
)

__all__ = [
    # Event Bus
    "EventBus",
    "Event", 
    "EventPriority",
    "EventScope",
    "EventStatus",
    "get_event_bus",
    "initialize_event_bus",
    "shutdown_event_bus",
    
    # Message Router
    "MessageRouter",
    "ServiceRole",
    "RoutingStrategy", 
    "MessageType",
    "RoutingRule",
    "ServiceEndpoint",
    "RoutingContext",
    "RoutedMessage",
    "get_message_router",
    "initialize_message_router",
    
    # Queue Manager
    "QueueManager",
    "MessageQueue",
    "QueueType",
    "QueueStrategy",
    "MessageStatus",
    "QueuedMessage", 
    "QueueConfiguration",
    "QueueMetrics",
    "get_queue_manager",
    "initialize_queue_manager",
    
    # Pub-Sub Coordinator
    "PubSubCoordinator",
    "Topic",
    "Subscription",
    "Publication",
    "SubscriptionType",
    "DeliveryMode",
    "TopicType", 
    "DeliveryReceipt",
    "get_pubsub_coordinator",
    "initialize_pubsub_coordinator",
    
    # Dead Letter Handler
    "DeadLetterHandler",
    "DeadLetterMessage",
    "FailureContext",
    "FailureReason",
    "RecoveryAction",
    "RecoveryPlan",
    "DeadLetterStats",
    "AlertLevel",
    "get_dead_letter_handler",
    "initialize_dead_letter_handler",
    
    # Redis Message Router (Phase 3)
    "RedisMessageRouter",
    "get_redis_message_router",
    
    # Horizontal Scaling Coordinator (Phase 3)
    "HorizontalScalingCoordinator",
    "ScalingPolicy",
    "InstanceMetrics", 
    "ScalingConfiguration",
    "get_horizontal_scaling_coordinator",
    
    # Circuit Breaker (Phase 3)
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerMetrics",
    "CircuitBreakerException",
    "CircuitBreakerManager",
    "CircuitState",
    "get_circuit_breaker_manager",
    "circuit_breaker",
    
    # Async Health Checker (Phase 3)
    "AsyncHealthCheckManager",
    "ServiceHealthChecker",
    "HealthCheckConfig",
    "HealthMetrics",
    "HealthStatus",
    "get_health_check_manager",
    "setup_default_health_checks",
    
    # Infrastructure Functions
    "initialize_messaging_infrastructure",
    "initialize_production_messaging_infrastructure",
    "shutdown_messaging_infrastructure",
    "get_messaging_stats"
]

# Version information
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Event-driven messaging infrastructure for TaxPoynt platform"

# Package metadata
PACKAGE_INFO = {
    "name": "taxpoynt_platform.core_platform.messaging",
    "version": __version__,
    "description": __description__,
    "components": [
        "Event Bus - Central event system",
        "Message Router - Role-based routing", 
        "Queue Manager - Message queue management",
        "Pub-Sub Coordinator - Publish-subscribe patterns",
        "Dead Letter Handler - Failed message processing",
        "Redis Message Router - Distributed scalable routing (Phase 3)",
        "Horizontal Scaling Coordinator - Auto-scaling management (Phase 3)",
        "Circuit Breaker - Service failure protection (Phase 3)",
        "Async Health Checker - Non-blocking health monitoring (Phase 3)"
    ],
    "features": [
        "Cross-service event communication",
        "Role-based message routing (SI/APP/Hybrid)",
        "Priority queue management",
        "Reliable message delivery",
        "Dead letter queue handling",
        "Message persistence",
        "Real-time monitoring",
        "Automatic recovery",
        "Poison message detection",
        "Redis-backed distributed state (Phase 3)",
        "Horizontal auto-scaling (Phase 3)",
        "Circuit breaker protection (Phase 3)",
        "Non-blocking health checks (Phase 3)",
        "1M+ daily transaction capability (Phase 3)"
    ]
}


async def initialize_messaging_infrastructure(
    enable_persistence: bool = True,
    max_workers: int = 10,
    storage_path: str = "./messaging_data"
) -> dict:
    """
    Initialize complete messaging infrastructure
    
    Returns dictionary with initialized components
    """
    from pathlib import Path
    
    storage_path = Path(storage_path)
    
    # Initialize Event Bus
    event_bus = await initialize_event_bus(
        max_workers=max_workers,
        enable_persistence=enable_persistence
    )
    
    # Initialize Message Router
    message_router = await initialize_message_router(event_bus)
    
    # Initialize Queue Manager  
    queue_manager = await initialize_queue_manager(storage_path / "queues")
    
    # Initialize Pub-Sub Coordinator
    pubsub_coordinator = await initialize_pubsub_coordinator(event_bus)
    
    # Initialize Dead Letter Handler
    dead_letter_handler = await initialize_dead_letter_handler(
        event_bus, 
        storage_path / "dead_letters"
    )
    
    return {
        "event_bus": event_bus,
        "message_router": message_router,
        "queue_manager": queue_manager,
        "pubsub_coordinator": pubsub_coordinator,
        "dead_letter_handler": dead_letter_handler
    }


async def initialize_production_messaging_infrastructure(
    redis_client=None,
    scaling_config: ScalingConfiguration = None
) -> dict:
    """
    Initialize Phase 3 production messaging infrastructure
    
    Features:
    - Redis-backed message routing
    - Horizontal scaling coordination  
    - Circuit breaker protection
    - Async health monitoring
    - 1M+ daily transaction capability
    
    Returns dictionary with initialized components
    """
    import redis.asyncio as redis
    import os
    
    # Get Redis client
    if redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    
    # Initialize Redis Message Router
    redis_message_router = get_redis_message_router(redis_client)
    await redis_message_router.initialize()
    
    # Initialize Horizontal Scaling Coordinator
    scaling_config = scaling_config or ScalingConfiguration()
    scaling_coordinator = get_horizontal_scaling_coordinator(redis_client, scaling_config)
    await scaling_coordinator.initialize()
    
    # Initialize Circuit Breaker Manager
    circuit_breaker_manager = get_circuit_breaker_manager(redis_client)
    
    # Initialize Async Health Check Manager
    health_check_manager = get_health_check_manager(redis_client)
    await setup_default_health_checks(health_check_manager)
    await health_check_manager.start_all_monitoring()
    
    return {
        "redis_message_router": redis_message_router,
        "scaling_coordinator": scaling_coordinator,
        "circuit_breaker_manager": circuit_breaker_manager,
        "health_check_manager": health_check_manager,
        "redis_client": redis_client
    }


async def shutdown_messaging_infrastructure():
    """Shutdown all messaging components"""
    try:
        # Get global instances
        event_bus = get_event_bus()
        message_router = get_message_router()
        queue_manager = get_queue_manager()
        pubsub_coordinator = get_pubsub_coordinator()
        dead_letter_handler = get_dead_letter_handler()
        
        # Shutdown in reverse order
        await dead_letter_handler.stop()
        await pubsub_coordinator.stop()
        await queue_manager.shutdown()
        # Message router doesn't have explicit shutdown
        await event_bus.stop()
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error during messaging infrastructure shutdown: {str(e)}")


def get_messaging_stats() -> dict:
    """Get comprehensive messaging statistics"""
    try:
        # This would be implemented to gather stats from all components
        # For now, return basic info
        return {
            "components_initialized": True,
            "version": __version__,
            "package_info": PACKAGE_INFO
        }
    except Exception:
        return {"error": "Could not gather messaging stats"}