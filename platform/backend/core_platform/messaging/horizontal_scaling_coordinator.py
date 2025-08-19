"""
TaxPoynt Platform - Horizontal Scaling Coordinator
=================================================
Manages multiple Redis-backed message router instances for horizontal scaling.
Implements load balancing, health monitoring, and auto-scaling for 1M+ daily transactions.
"""

import asyncio
import json
import logging
import uuid
import redis.asyncio as redis
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .redis_message_router import RedisMessageRouter, ServiceRole
from .message_router import RoutedMessage, MessageType, RoutingStrategy

logger = logging.getLogger(__name__)


class ScalingPolicy(str, Enum):
    """Auto-scaling policies"""
    MANUAL = "manual"              # Manual scaling only
    CPU_BASED = "cpu_based"        # Scale based on CPU usage
    QUEUE_BASED = "queue_based"    # Scale based on message queue depth
    LATENCY_BASED = "latency_based"  # Scale based on routing latency
    HYBRID = "hybrid"              # Multiple metrics


@dataclass
class InstanceMetrics:
    """Metrics for a router instance"""
    instance_id: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    messages_per_second: float = 0.0
    routing_latency_ms: float = 0.0
    queue_depth: int = 0
    health_score: float = 1.0
    last_heartbeat: datetime = None
    uptime_seconds: float = 0.0
    error_rate: float = 0.0


@dataclass
class ScalingConfiguration:
    """Auto-scaling configuration"""
    min_instances: int = 1
    max_instances: int = 10
    target_cpu_percentage: float = 70.0
    target_messages_per_second: float = 1000.0
    target_latency_ms: float = 100.0
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    cooldown_period_seconds: int = 300
    policy: ScalingPolicy = ScalingPolicy.HYBRID


class HorizontalScalingCoordinator:
    """
    Coordinates multiple Redis message router instances for horizontal scaling
    
    Features:
    - Instance lifecycle management
    - Load balancing across instances
    - Health monitoring and failover
    - Auto-scaling based on load metrics
    - Message distribution strategies
    - Performance optimization
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None,
                 scaling_config: Optional[ScalingConfiguration] = None):
        """Initialize horizontal scaling coordinator"""
        self.redis = redis_client or self._get_redis_client()
        self.scaling_config = scaling_config or ScalingConfiguration()
        
        # Coordinator identification
        self.coordinator_id = f"coordinator_{uuid.uuid4().hex[:8]}"
        self.startup_time = datetime.now(timezone.utc)
        
        # Instance management
        self.active_instances: Dict[str, RedisMessageRouter] = {}
        self.instance_metrics: Dict[str, InstanceMetrics] = {}
        self.instance_load_distribution: Dict[str, float] = {}
        
        # Scaling state
        self.last_scaling_action = None
        self.scaling_in_progress = False
        self.target_instance_count = self.scaling_config.min_instances
        
        # Redis keys
        self.prefix = "taxpoynt:scaling_coordinator"
        self.coordinator_key = f"{self.prefix}:coordinator:{self.coordinator_id}"
        self.instances_registry_key = f"{self.prefix}:instances_registry"
        self.metrics_key = f"{self.prefix}:metrics"
        self.scaling_events_key = f"{self.prefix}:scaling_events"
        self.load_balancer_key = f"{self.prefix}:load_balancer"
        
        # Background tasks
        self._monitoring_task = None
        self._autoscaling_task = None
        self._health_check_task = None
        self._metrics_collection_task = None
        
        # Statistics
        self.coordinator_stats = {
            "instances_created": 0,
            "instances_destroyed": 0,
            "scaling_actions": 0,
            "failovers": 0,
            "total_messages_distributed": 0,
            "load_balancing_decisions": 0
        }
        
        logger.info(f"Horizontal Scaling Coordinator initialized - ID: {self.coordinator_id}")
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client connection"""
        try:
            import os
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            
            return redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    async def initialize(self):
        """Initialize the scaling coordinator"""
        logger.info("Initializing Horizontal Scaling Coordinator")
        
        try:
            # Test Redis connection
            await self.redis.ping()
            
            # Register coordinator
            await self._register_coordinator()
            
            # Start with minimum instances
            await self._ensure_minimum_instances()
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info(f"Scaling Coordinator initialized with {len(self.active_instances)} instances")
            
        except Exception as e:
            logger.error(f"Scaling Coordinator initialization failed: {e}")
            raise
    
    async def _register_coordinator(self):
        """Register this coordinator in Redis"""
        coordinator_data = {
            "coordinator_id": self.coordinator_id,
            "startup_time": self.startup_time.isoformat(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "target_instances": self.target_instance_count,
            "scaling_policy": self.scaling_config.policy.value
        }
        
        await self.redis.hset(self.coordinator_key, mapping=coordinator_data)
        await self.redis.expire(self.coordinator_key, 600)  # 10 min TTL
    
    async def _ensure_minimum_instances(self):
        """Ensure minimum number of instances are running"""
        current_count = len(self.active_instances)
        needed_count = max(0, self.scaling_config.min_instances - current_count)
        
        for i in range(needed_count):
            await self._create_router_instance()
    
    async def _create_router_instance(self) -> str:
        """Create a new router instance"""
        try:
            instance_id = f"router_{uuid.uuid4().hex[:8]}"
            
            # Create Redis message router
            router = RedisMessageRouter(
                redis_client=self.redis,
                instance_id=instance_id
            )
            
            # Initialize the router
            await router.initialize()
            
            # Add to active instances
            self.active_instances[instance_id] = router
            
            # Initialize metrics
            self.instance_metrics[instance_id] = InstanceMetrics(
                instance_id=instance_id,
                last_heartbeat=datetime.now(timezone.utc)
            )
            
            # Initialize load distribution
            self.instance_load_distribution[instance_id] = 0.0
            
            # Register in Redis
            await self._register_instance(instance_id)
            
            # Update stats
            self.coordinator_stats["instances_created"] += 1
            
            logger.info(f"Created router instance: {instance_id}")
            return instance_id
            
        except Exception as e:
            logger.error(f"Failed to create router instance: {e}")
            raise
    
    async def _register_instance(self, instance_id: str):
        """Register instance in Redis registry"""
        instance_data = {
            "instance_id": instance_id,
            "coordinator_id": self.coordinator_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "load_score": 0.0
        }
        
        await self.redis.hset(
            f"{self.instances_registry_key}:{instance_id}",
            mapping=instance_data
        )
    
    async def _destroy_router_instance(self, instance_id: str):
        """Destroy a router instance"""
        try:
            if instance_id in self.active_instances:
                router = self.active_instances[instance_id]
                
                # Graceful shutdown
                await router.shutdown()
                
                # Remove from tracking
                del self.active_instances[instance_id]
                del self.instance_metrics[instance_id]
                del self.instance_load_distribution[instance_id]
                
                # Remove from Redis registry
                await self.redis.delete(f"{self.instances_registry_key}:{instance_id}")
                
                # Update stats
                self.coordinator_stats["instances_destroyed"] += 1
                
                logger.info(f"Destroyed router instance: {instance_id}")
                
        except Exception as e:
            logger.error(f"Failed to destroy router instance {instance_id}: {e}")
    
    async def _start_background_tasks(self):
        """Start background monitoring and scaling tasks"""
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._autoscaling_task = asyncio.create_task(self._autoscaling_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        self._metrics_collection_task = asyncio.create_task(self._metrics_collection_loop())
    
    async def _monitoring_loop(self):
        """Monitor coordinator status and update heartbeat"""
        while True:
            try:
                # Update coordinator heartbeat
                await self.redis.hset(
                    self.coordinator_key,
                    "last_heartbeat",
                    datetime.now(timezone.utc).isoformat()
                )
                await self.redis.expire(self.coordinator_key, 600)
                
                # Update target instance count
                await self.redis.hset(
                    self.coordinator_key,
                    "target_instances",
                    str(self.target_instance_count)
                )
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(30)
    
    async def _metrics_collection_loop(self):
        """Collect metrics from all instances"""
        while True:
            try:
                for instance_id, router in self.active_instances.items():
                    # Get router statistics
                    stats = await router.get_routing_statistics()
                    
                    if "local_instance" in stats:
                        local_stats = stats["local_instance"]
                        
                        # Update instance metrics
                        metrics = self.instance_metrics[instance_id]
                        metrics.messages_per_second = self._calculate_messages_per_second(local_stats)
                        metrics.routing_latency_ms = self._calculate_routing_latency(local_stats)
                        metrics.error_rate = self._calculate_error_rate(local_stats)
                        metrics.uptime_seconds = local_stats.get("instance_uptime", 0)
                        metrics.last_heartbeat = datetime.now(timezone.utc)
                        
                        # Calculate health score
                        metrics.health_score = self._calculate_health_score(metrics)
                        
                        # Store metrics in Redis
                        await self._store_instance_metrics(instance_id, metrics)
                
                await asyncio.sleep(10)  # Collect metrics every 10 seconds
                
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(10)
    
    async def _calculate_messages_per_second(self, stats: Dict[str, Any]) -> float:
        """Calculate messages per second for an instance"""
        try:
            messages_routed = stats.get("messages_routed", 0)
            uptime = stats.get("instance_uptime", 1)
            return messages_routed / max(uptime, 1)
        except:
            return 0.0
    
    async def _calculate_routing_latency(self, stats: Dict[str, Any]) -> float:
        """Calculate average routing latency"""
        # This would require additional timing metrics in the router
        # For now, return a placeholder based on success rate
        try:
            total_messages = stats.get("messages_routed", 0)
            successful = stats.get("successful_deliveries", 0)
            if total_messages > 0:
                success_rate = successful / total_messages
                # Higher success rate = lower latency (simplified)
                return max(10, 200 * (1 - success_rate))
            return 50.0
        except:
            return 100.0
    
    def _calculate_error_rate(self, stats: Dict[str, Any]) -> float:
        """Calculate error rate for an instance"""
        try:
            total_messages = stats.get("messages_routed", 0)
            failures = stats.get("routing_failures", 0) + stats.get("failed_deliveries", 0)
            if total_messages > 0:
                return failures / total_messages
            return 0.0
        except:
            return 0.0
    
    def _calculate_health_score(self, metrics: InstanceMetrics) -> float:
        """Calculate overall health score for an instance"""
        try:
            # Health score based on multiple factors
            latency_score = max(0, 1 - (metrics.routing_latency_ms / 1000))  # Lower latency = higher score
            error_score = max(0, 1 - metrics.error_rate)  # Lower error rate = higher score
            
            # Heartbeat freshness
            if metrics.last_heartbeat:
                heartbeat_age = (datetime.now(timezone.utc) - metrics.last_heartbeat).total_seconds()
                heartbeat_score = max(0, 1 - (heartbeat_age / 300))  # 5 min max age
            else:
                heartbeat_score = 0.0
            
            # Weighted average
            health_score = (
                0.3 * latency_score +
                0.4 * error_score +
                0.3 * heartbeat_score
            )
            
            return max(0.0, min(1.0, health_score))
            
        except:
            return 0.5  # Default neutral score
    
    async def _store_instance_metrics(self, instance_id: str, metrics: InstanceMetrics):
        """Store instance metrics in Redis"""
        try:
            metrics_data = {
                "instance_id": metrics.instance_id,
                "cpu_usage": str(metrics.cpu_usage),
                "memory_usage": str(metrics.memory_usage),
                "messages_per_second": str(metrics.messages_per_second),
                "routing_latency_ms": str(metrics.routing_latency_ms),
                "queue_depth": str(metrics.queue_depth),
                "health_score": str(metrics.health_score),
                "last_heartbeat": metrics.last_heartbeat.isoformat() if metrics.last_heartbeat else "",
                "uptime_seconds": str(metrics.uptime_seconds),
                "error_rate": str(metrics.error_rate),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.redis.hset(
                f"{self.metrics_key}:{instance_id}",
                mapping=metrics_data
            )
            await self.redis.expire(f"{self.metrics_key}:{instance_id}", 3600)  # 1 hour TTL
            
        except Exception as e:
            logger.error(f"Error storing metrics for {instance_id}: {e}")
    
    async def _health_check_loop(self):
        """Monitor instance health and handle failures"""
        while True:
            try:
                unhealthy_instances = []
                
                for instance_id, metrics in self.instance_metrics.items():
                    # Check if instance is unhealthy
                    if metrics.health_score < 0.3:  # Health threshold
                        unhealthy_instances.append(instance_id)
                        logger.warning(f"Instance {instance_id} is unhealthy (score: {metrics.health_score})")
                    
                    # Check heartbeat timeout
                    if metrics.last_heartbeat:
                        heartbeat_age = (datetime.now(timezone.utc) - metrics.last_heartbeat).total_seconds()
                        if heartbeat_age > 300:  # 5 minutes timeout
                            unhealthy_instances.append(instance_id)
                            logger.warning(f"Instance {instance_id} heartbeat timeout ({heartbeat_age}s)")
                
                # Handle unhealthy instances
                for instance_id in set(unhealthy_instances):
                    await self._handle_unhealthy_instance(instance_id)
                
                await asyncio.sleep(60)  # Health check every minute
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)
    
    async def _handle_unhealthy_instance(self, instance_id: str):
        """Handle an unhealthy instance"""
        try:
            logger.info(f"Handling unhealthy instance: {instance_id}")
            
            # Mark as unhealthy in load balancer
            self.instance_load_distribution[instance_id] = 0.0
            
            # If we have enough healthy instances, destroy the unhealthy one
            healthy_count = len([
                iid for iid, metrics in self.instance_metrics.items()
                if metrics.health_score >= 0.3 and iid != instance_id
            ])
            
            if healthy_count >= self.scaling_config.min_instances:
                await self._destroy_router_instance(instance_id)
                self.coordinator_stats["failovers"] += 1
                
                # Create a replacement if needed
                if len(self.active_instances) < self.target_instance_count:
                    await self._create_router_instance()
            
        except Exception as e:
            logger.error(f"Error handling unhealthy instance {instance_id}: {e}")
    
    async def _autoscaling_loop(self):
        """Auto-scaling logic based on load metrics"""
        while True:
            try:
                if self.scaling_config.policy == ScalingPolicy.MANUAL:
                    await asyncio.sleep(60)
                    continue
                
                # Check if cooldown period has passed
                if (self.last_scaling_action and 
                    (datetime.now(timezone.utc) - self.last_scaling_action).total_seconds() < 
                    self.scaling_config.cooldown_period_seconds):
                    await asyncio.sleep(30)
                    continue
                
                # Calculate scaling decision
                scaling_decision = await self._calculate_scaling_decision()
                
                if scaling_decision != 0 and not self.scaling_in_progress:
                    await self._execute_scaling_decision(scaling_decision)
                
                await asyncio.sleep(30)  # Check scaling every 30 seconds
                
            except Exception as e:
                logger.error(f"Auto-scaling loop error: {e}")
                await asyncio.sleep(30)
    
    async def _calculate_scaling_decision(self) -> int:
        """Calculate scaling decision based on metrics"""
        try:
            current_count = len(self.active_instances)
            healthy_instances = [
                metrics for metrics in self.instance_metrics.values()
                if metrics.health_score >= 0.3
            ]
            
            if not healthy_instances:
                return 1  # Scale up if no healthy instances
            
            # Calculate average metrics
            avg_messages_per_second = sum(m.messages_per_second for m in healthy_instances) / len(healthy_instances)
            avg_latency = sum(m.routing_latency_ms for m in healthy_instances) / len(healthy_instances)
            avg_error_rate = sum(m.error_rate for m in healthy_instances) / len(healthy_instances)
            
            # Scaling factors
            message_load_factor = avg_messages_per_second / self.scaling_config.target_messages_per_second
            latency_factor = avg_latency / self.scaling_config.target_latency_ms
            error_factor = avg_error_rate / 0.05  # Target 5% error rate
            
            # Combined load factor
            load_factor = max(message_load_factor, latency_factor, error_factor)
            
            # Scale up if load is high
            if load_factor > self.scaling_config.scale_up_threshold:
                if current_count < self.scaling_config.max_instances:
                    return 1  # Scale up
            
            # Scale down if load is low
            elif load_factor < self.scaling_config.scale_down_threshold:
                if current_count > self.scaling_config.min_instances:
                    return -1  # Scale down
            
            return 0  # No scaling needed
            
        except Exception as e:
            logger.error(f"Error calculating scaling decision: {e}")
            return 0
    
    async def _execute_scaling_decision(self, decision: int):
        """Execute scaling decision"""
        try:
            self.scaling_in_progress = True
            
            if decision > 0:
                # Scale up
                logger.info("Scaling up: creating new router instance")
                await self._create_router_instance()
                self.target_instance_count += 1
                
            elif decision < 0:
                # Scale down - remove least healthy instance
                worst_instance = min(
                    self.instance_metrics.items(),
                    key=lambda x: x[1].health_score
                )[0]
                
                logger.info(f"Scaling down: removing instance {worst_instance}")
                await self._destroy_router_instance(worst_instance)
                self.target_instance_count -= 1
            
            # Record scaling action
            self.last_scaling_action = datetime.now(timezone.utc)
            self.coordinator_stats["scaling_actions"] += 1
            
            # Log scaling event
            await self._log_scaling_event(decision)
            
        finally:
            self.scaling_in_progress = False
    
    async def _log_scaling_event(self, decision: int):
        """Log scaling event to Redis"""
        try:
            event_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "coordinator_id": self.coordinator_id,
                "decision": decision,
                "instance_count_before": len(self.active_instances) - decision,
                "instance_count_after": len(self.active_instances),
                "target_count": self.target_instance_count,
                "scaling_reason": "auto_scaling"
            }
            
            event_id = f"scaling_{uuid.uuid4().hex[:8]}"
            await self.redis.hset(
                f"{self.scaling_events_key}:{event_id}",
                mapping=event_data
            )
            await self.redis.expire(f"{self.scaling_events_key}:{event_id}", 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error logging scaling event: {e}")
    
    async def distribute_message(self, message: RoutedMessage) -> List[str]:
        """Distribute message using load balancing across instances"""
        try:
            if not self.active_instances:
                logger.error("No active router instances available")
                return []
            
            # Select best instance based on load distribution
            selected_instance_id = await self._select_instance_for_message(message)
            
            if selected_instance_id not in self.active_instances:
                logger.error(f"Selected instance {selected_instance_id} not available")
                return []
            
            # Route message through selected instance
            router = self.active_instances[selected_instance_id]
            targets = await router.route_message(message)
            
            # Update load distribution
            self.instance_load_distribution[selected_instance_id] += 1.0
            self.coordinator_stats["total_messages_distributed"] += 1
            self.coordinator_stats["load_balancing_decisions"] += 1
            
            return targets
            
        except Exception as e:
            logger.error(f"Message distribution error: {e}")
            return []
    
    async def _select_instance_for_message(self, message: RoutedMessage) -> str:
        """Select best instance for routing a message"""
        # Calculate load scores for healthy instances
        candidate_instances = {}
        
        for instance_id, metrics in self.instance_metrics.items():
            if metrics.health_score >= 0.3:  # Only healthy instances
                # Lower score = better choice
                load_score = (
                    0.4 * metrics.routing_latency_ms / 1000 +  # Latency factor
                    0.3 * metrics.error_rate +                # Error factor
                    0.2 * self.instance_load_distribution.get(instance_id, 0) / 1000 +  # Load factor
                    0.1 * (1 - metrics.health_score)          # Health factor
                )
                candidate_instances[instance_id] = load_score
        
        if not candidate_instances:
            # Fallback to any available instance
            return list(self.active_instances.keys())[0]
        
        # Select instance with lowest load score
        best_instance = min(candidate_instances.items(), key=lambda x: x[1])[0]
        return best_instance
    
    async def get_scaling_status(self) -> Dict[str, Any]:
        """Get comprehensive scaling status"""
        try:
            # Instance status
            instance_status = {}
            for instance_id, metrics in self.instance_metrics.items():
                instance_status[instance_id] = {
                    "health_score": metrics.health_score,
                    "messages_per_second": metrics.messages_per_second,
                    "routing_latency_ms": metrics.routing_latency_ms,
                    "error_rate": metrics.error_rate,
                    "uptime_seconds": metrics.uptime_seconds,
                    "load_distribution": self.instance_load_distribution.get(instance_id, 0.0),
                    "last_heartbeat": metrics.last_heartbeat.isoformat() if metrics.last_heartbeat else None
                }
            
            # Scaling configuration
            scaling_status = {
                "coordinator_id": self.coordinator_id,
                "active_instances": len(self.active_instances),
                "target_instances": self.target_instance_count,
                "min_instances": self.scaling_config.min_instances,
                "max_instances": self.scaling_config.max_instances,
                "scaling_policy": self.scaling_config.policy.value,
                "scaling_in_progress": self.scaling_in_progress,
                "last_scaling_action": self.last_scaling_action.isoformat() if self.last_scaling_action else None,
                "coordinator_uptime": (datetime.now(timezone.utc) - self.startup_time).total_seconds(),
                "coordinator_stats": self.coordinator_stats,
                "instances": instance_status
            }
            
            return scaling_status
            
        except Exception as e:
            logger.error(f"Error getting scaling status: {e}")
            return {"error": str(e)}
    
    async def manual_scale(self, target_count: int) -> bool:
        """Manually scale to target instance count"""
        try:
            if target_count < self.scaling_config.min_instances:
                target_count = self.scaling_config.min_instances
            elif target_count > self.scaling_config.max_instances:
                target_count = self.scaling_config.max_instances
            
            current_count = len(self.active_instances)
            difference = target_count - current_count
            
            if difference > 0:
                # Scale up
                for _ in range(difference):
                    await self._create_router_instance()
            elif difference < 0:
                # Scale down
                instances_to_remove = sorted(
                    self.instance_metrics.items(),
                    key=lambda x: x[1].health_score
                )[:abs(difference)]
                
                for instance_id, _ in instances_to_remove:
                    await self._destroy_router_instance(instance_id)
            
            self.target_instance_count = target_count
            self.last_scaling_action = datetime.now(timezone.utc)
            self.coordinator_stats["scaling_actions"] += 1
            
            await self._log_scaling_event(difference)
            
            logger.info(f"Manual scaling: {current_count} -> {target_count} instances")
            return True
            
        except Exception as e:
            logger.error(f"Manual scaling error: {e}")
            return False
    
    async def shutdown(self):
        """Graceful shutdown of the scaling coordinator"""
        logger.info("Shutting down Horizontal Scaling Coordinator")
        
        try:
            # Cancel background tasks
            for task in [self._monitoring_task, self._autoscaling_task, 
                        self._health_check_task, self._metrics_collection_task]:
                if task:
                    task.cancel()
            
            # Shutdown all router instances
            for instance_id in list(self.active_instances.keys()):
                await self._destroy_router_instance(instance_id)
            
            # Update coordinator status
            await self.redis.hset(self.coordinator_key, "status", "shutdown")
            
            # Close Redis connection
            await self.redis.close()
            
            logger.info("Horizontal Scaling Coordinator shutdown complete")
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")


def get_horizontal_scaling_coordinator(redis_client: Optional[redis.Redis] = None,
                                     scaling_config: Optional[ScalingConfiguration] = None) -> HorizontalScalingCoordinator:
    """Factory function to create horizontal scaling coordinator"""
    return HorizontalScalingCoordinator(redis_client, scaling_config)