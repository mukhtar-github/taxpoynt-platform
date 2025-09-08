"""
TaxPoynt Platform - Redis-Backed Message Router
==============================================
Production-grade message router with Redis state management for horizontal scaling.
Replaces in-memory routing with distributed state for 1M+ daily transactions.
"""

import asyncio
import json
import logging
import uuid
import redis.asyncio as redis
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# Import existing message router classes
from .message_router import (
    ServiceRole, RoutingStrategy, MessageType, RoutingRule, 
    ServiceEndpoint, RoutingContext, RoutedMessage, MessageRouter
)
from .event_bus import Event, EventBus, EventScope, EventPriority, get_event_bus

logger = logging.getLogger(__name__)


class RedisMessageRouter(MessageRouter):
    """
    Redis-backed Message Router for horizontal scaling
    
    Features:
    - Distributed routing state across multiple instances
    - Redis-backed service discovery
    - Horizontal scaling support
    - High-availability message routing
    - Load balancing across instances
    - Persistent routing rules and state
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None, 
                 event_bus: Optional[EventBus] = None, 
                 instance_id: Optional[str] = None):
        """Initialize Redis-backed message router"""
        super().__init__(event_bus)
        
        # Redis connection
        self.redis = redis_client or self._get_redis_client()
        
        # Instance identification for scaling
        self.instance_id = instance_id or f"router_{uuid.uuid4().hex[:8]}"
        self.instance_startup = datetime.now(timezone.utc)
        
        # Redis key prefixes for namespacing
        self.prefix = "taxpoynt:message_router"
        self.routing_rules_key = f"{self.prefix}:routing_rules"
        self.service_endpoints_key = f"{self.prefix}:service_endpoints"
        self.role_mappings_key = f"{self.prefix}:role_mappings"
        self.routing_table_key = f"{self.prefix}:routing_table"
        self.active_routes_key = f"{self.prefix}:active_routes"
        self.load_metrics_key = f"{self.prefix}:load_metrics"
        self.round_robin_key = f"{self.prefix}:round_robin_state"
        self.instances_key = f"{self.prefix}:instances"
        self.stats_key = f"{self.prefix}:stats"
        
        # Local cache for performance
        self._local_cache = {
            "routing_rules": {},
            "service_endpoints": {},
            "role_mappings": {},
            "last_cache_update": None
        }
        self._cache_ttl = 60  # Cache TTL in seconds
        
        # Background tasks
        self._maintenance_task = None
        self._health_check_task = None
        
        logger.info(f"Redis Message Router initialized - Instance: {self.instance_id}")
    
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
        """Initialize Redis-backed message router"""
        if self.is_initialized:
            return
        
        logger.info(f"Initializing Redis Message Router - Instance: {self.instance_id}")
        
        try:
            # Test Redis connection
            await self.redis.ping()
            logger.info("Redis connection established")
            
            # Register this instance
            await self._register_instance()
            
            # Load existing state from Redis
            await self._load_state_from_redis()
            
            # Start background maintenance tasks
            await self._start_background_tasks()
            
            # Initialize default routing rules
            await self._setup_default_routing_rules()
            
            self.is_initialized = True
            logger.info("Redis Message Router initialization complete")
            
        except Exception as e:
            logger.error(f"Redis Message Router initialization failed: {e}")
            raise
    
    async def _register_instance(self):
        """Register this router instance in Redis"""
        instance_data = {
            "instance_id": self.instance_id,
            "startup_time": self.instance_startup.isoformat(),
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "status": "active",
            "version": "1.0.0"
        }
        
        await self.redis.hset(
            f"{self.instances_key}:{self.instance_id}",
            mapping=instance_data
        )
        await self.redis.expire(f"{self.instances_key}:{self.instance_id}", 300)  # 5 min TTL
    
    async def _load_state_from_redis(self):
        """Load routing state from Redis"""
        try:
            # Load routing rules
            rules_data = await self.redis.hgetall(self.routing_rules_key)
            for rule_id, rule_json in rules_data.items():
                rule_dict = json.loads(rule_json)
                self.routing_rules[rule_id] = RoutingRule(**rule_dict)
            
            # Load service endpoints
            endpoints_data = await self.redis.hgetall(self.service_endpoints_key)
            for service_id, endpoint_json in endpoints_data.items():
                endpoint_dict = json.loads(endpoint_json)
                # Convert string back to enum
                endpoint_dict["role"] = ServiceRole(endpoint_dict["role"])
                self.service_endpoints[service_id] = ServiceEndpoint(**endpoint_dict)
            
            # Load role mappings
            mappings_data = await self.redis.hgetall(self.role_mappings_key)
            for role_str, services_json in mappings_data.items():
                role = ServiceRole(role_str)
                self.role_mappings[role] = json.loads(services_json)
            
            # Load routing table
            table_data = await self.redis.hgetall(self.routing_table_key)
            for key, routes_json in table_data.items():
                self.routing_table[key] = json.loads(routes_json)
            
            # Load round-robin state
            rr_data = await self.redis.hgetall(self.round_robin_key)
            for key, index_str in rr_data.items():
                self.round_robin_state[key] = int(index_str)
            
            # Update local cache
            self._local_cache["last_cache_update"] = datetime.now(timezone.utc)
            
            logger.info(f"Loaded state from Redis: {len(self.routing_rules)} rules, "
                       f"{len(self.service_endpoints)} endpoints")
            
        except Exception as e:
            logger.error(f"Error loading state from Redis: {e}")
            # Continue with empty state if Redis load fails
    
    async def _start_background_tasks(self):
        """Start background maintenance tasks"""
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _maintenance_loop(self):
        """Background maintenance for Redis state"""
        while True:
            try:
                # Update instance heartbeat
                await self.redis.hset(
                    f"{self.instances_key}:{self.instance_id}",
                    "last_heartbeat",
                    datetime.now(timezone.utc).isoformat()
                )
                await self.redis.expire(f"{self.instances_key}:{self.instance_id}", 300)
                
                # Clean up expired routes
                await self._cleanup_expired_routes()
                
                # Update routing statistics
                await self._update_routing_stats()
                
                # Sleep for 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Maintenance loop error: {e}")
                await asyncio.sleep(30)
    
    async def _health_check_loop(self):
        """Background health checking for services"""
        while True:
            try:
                # Check service health
                for service_id, endpoint in self.service_endpoints.items():
                    # Basic health check - could be enhanced with actual HTTP checks
                    last_seen = endpoint.last_seen or datetime.now(timezone.utc)
                    if (datetime.now(timezone.utc) - last_seen).total_seconds() > 300:
                        endpoint.is_healthy = False
                        endpoint.status = "unhealthy"
                        await self._persist_service_endpoint(service_id, endpoint)
                
                await asyncio.sleep(60)  # Health check every minute
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_routes(self):
        """Clean up expired active routes"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_routes = []
            
            # Get all active routes
            routes_data = await self.redis.hgetall(self.active_routes_key)
            
            for route_id, route_json in routes_data.items():
                route_dict = json.loads(route_json)
                if route_dict.get("expiry"):
                    expiry = datetime.fromisoformat(route_dict["expiry"])
                    if current_time > expiry:
                        expired_routes.append(route_id)
            
            # Remove expired routes
            if expired_routes:
                await self.redis.hdel(self.active_routes_key, *expired_routes)
                logger.info(f"Cleaned up {len(expired_routes)} expired routes")
                
        except Exception as e:
            logger.error(f"Route cleanup error: {e}")
    
    async def _update_routing_stats(self):
        """Update routing statistics in Redis"""
        try:
            stats_data = {
                "instance_id": self.instance_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **self.routing_stats
            }
            
            await self.redis.hset(
                f"{self.stats_key}:{self.instance_id}",
                mapping={k: json.dumps(v) if isinstance(v, dict) else str(v) 
                        for k, v in stats_data.items()}
            )
            await self.redis.expire(f"{self.stats_key}:{self.instance_id}", 3600)
            
        except Exception as e:
            logger.error(f"Stats update error: {e}")
    
    async def register_service(
        self, 
        service_name: str = None,
        service_id: str = None, 
        endpoint: ServiceEndpoint = None,
        service_role: ServiceRole = None,
        callback: callable = None,
        priority: int = 0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """Register a service endpoint with Redis persistence"""
        # Handle backward compatibility
        if service_name and not service_id:
            service_id = service_name
        
        if endpoint is None and service_role:
            # Create endpoint from individual parameters
            from .message_router import ServiceEndpoint
            endpoint = ServiceEndpoint(
                service_id=service_id,
                name=service_name or service_id,
                role=service_role,
                callback=callback,
                priority=priority,
                tags=tags or [],
                metadata=metadata or {}
            )
        
        if not service_id or not endpoint:
            raise ValueError("Either service_id and endpoint, or service_name and service_role must be provided")
        
        # Update local state
        self.service_endpoints[service_id] = endpoint
        
        # Add to role mapping
        if endpoint.role not in self.role_mappings:
            self.role_mappings[endpoint.role] = []
        if service_id not in self.role_mappings[endpoint.role]:
            self.role_mappings[endpoint.role].append(service_id)
        
        # Persist to Redis
        await self._persist_service_endpoint(service_id, endpoint)
        await self._persist_role_mappings()
        
        logger.info(f"Registered service {service_id} with role {endpoint.role}")
        return service_id
    
    async def _persist_service_endpoint(self, service_id: str, endpoint: ServiceEndpoint):
        """Persist service endpoint to Redis"""
        endpoint_dict = asdict(endpoint)
        # Convert enum to string for JSON serialization
        endpoint_dict["role"] = endpoint.role.value
        endpoint_dict["last_seen"] = endpoint.last_seen.isoformat() if endpoint.last_seen else None
        
        await self.redis.hset(
            self.service_endpoints_key,
            service_id,
            json.dumps(endpoint_dict)
        )
    
    async def _persist_role_mappings(self):
        """Persist role mappings to Redis"""
        mappings_data = {
            role.value: json.dumps(services)
            for role, services in self.role_mappings.items()
        }
        await self.redis.delete(self.role_mappings_key)
        if mappings_data:
            await self.redis.hset(self.role_mappings_key, mapping=mappings_data)
    
    async def add_routing_rule(self, rule: RoutingRule):
        """Add routing rule with Redis persistence"""
        rule_id = f"{rule.source_role}_{rule.target_role}_{uuid.uuid4().hex[:8]}"
        
        # Update local state
        self.routing_rules[rule_id] = rule
        
        # Persist to Redis
        rule_dict = asdict(rule)
        # Convert enums to strings
        rule_dict["source_role"] = rule.source_role.value
        rule_dict["target_role"] = rule.target_role.value if rule.target_role else None
        rule_dict["strategy"] = rule.strategy.value
        rule_dict["message_pattern"] = rule.message_pattern if hasattr(rule, 'message_pattern') else ""
        
        await self.redis.hset(
            self.routing_rules_key,
            rule_id,
            json.dumps(rule_dict)
        )
        
        logger.info(f"Added routing rule: {rule_id}")
        return rule_id
    
    async def route_message(self, message: RoutedMessage) -> List[str]:
        """Route message using Redis-backed state"""
        try:
            # Update routing statistics
            self.routing_stats["messages_routed"] += 1
            
            # Find applicable routing rules
            applicable_rules = await self._find_applicable_rules(message)
            
            if not applicable_rules:
                logger.warning(f"No routing rules found for message {message.message_id}")
                self.routing_stats["routing_failures"] += 1
                return []
            
            # Route to targets based on rules
            targets = []
            for rule in applicable_rules:
                rule_targets = await self._route_by_rule(message, rule)
                targets.extend(rule_targets)
            
            # Remove duplicates while preserving order
            unique_targets = []
            seen = set()
            for target in targets:
                if target not in seen:
                    unique_targets.append(target)
                    seen.add(target)
            
            # Store active route
            await self._store_active_route(message)
            
            # Update message route history
            message.route_history.extend(unique_targets)
            
            if unique_targets:
                self.routing_stats["successful_deliveries"] += len(unique_targets)
                logger.info(f"Routed message {message.message_id} to {len(unique_targets)} targets")
            else:
                self.routing_stats["failed_deliveries"] += 1
                logger.warning(f"Failed to route message {message.message_id}")
            
            return unique_targets
            
        except Exception as e:
            logger.error(f"Message routing error: {e}")
            self.routing_stats["routing_failures"] += 1
            return []
    
    async def _store_active_route(self, message: RoutedMessage):
        """Store active route in Redis"""
        route_data = {
            "message_id": message.message_id,
            "message_type": message.message_type.value,
            "routing_context": asdict(message.routing_context),
            "timestamp": message.timestamp.isoformat(),
            "expiry": message.expiry.isoformat() if message.expiry else None,
            "route_history": message.route_history
        }
        
        await self.redis.hset(
            self.active_routes_key,
            message.message_id,
            json.dumps(route_data)
        )
        
        # Set expiry for the route record
        if message.expiry:
            ttl = int((message.expiry - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                await self.redis.expire(f"{self.active_routes_key}", ttl)
    
    async def get_routing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics across all instances"""
        try:
            # Get local stats
            local_stats = self.routing_stats.copy()
            local_stats["instance_id"] = self.instance_id
            local_stats["instance_uptime"] = (datetime.now(timezone.utc) - self.instance_startup).total_seconds()
            
            # Get stats from all instances
            all_instances = await self.redis.keys(f"{self.stats_key}:*")
            cluster_stats = {
                "total_messages_routed": 0,
                "total_routing_failures": 0,
                "total_successful_deliveries": 0,
                "total_failed_deliveries": 0,
                "active_instances": len(all_instances),
                "instances": []
            }
            
            for instance_key in all_instances:
                instance_data = await self.redis.hgetall(instance_key)
                if instance_data:
                    instance_stats = {
                        "instance_id": instance_data.get("instance_id"),
                        "timestamp": instance_data.get("timestamp"),
                        "messages_routed": int(instance_data.get("messages_routed", 0)),
                        "routing_failures": int(instance_data.get("routing_failures", 0)),
                        "successful_deliveries": int(instance_data.get("successful_deliveries", 0)),
                        "failed_deliveries": int(instance_data.get("failed_deliveries", 0))
                    }
                    
                    cluster_stats["instances"].append(instance_stats)
                    cluster_stats["total_messages_routed"] += instance_stats["messages_routed"]
                    cluster_stats["total_routing_failures"] += instance_stats["routing_failures"]
                    cluster_stats["total_successful_deliveries"] += instance_stats["successful_deliveries"]
                    cluster_stats["total_failed_deliveries"] += instance_stats["failed_deliveries"]
            
            return {
                "local_instance": local_stats,
                "cluster_wide": cluster_stats,
                "redis_info": {
                    "routing_rules_count": await self.redis.hlen(self.routing_rules_key),
                    "service_endpoints_count": await self.redis.hlen(self.service_endpoints_key),
                    "active_routes_count": await self.redis.hlen(self.active_routes_key)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting routing statistics: {e}")
            return {"error": str(e)}
    
    async def _setup_default_routing_rules(self):
        """Setup default routing rules for the platform"""
        default_rules = [
            # API Gateway to SI Banking Operations
            RoutingRule(
                rule_id="api_gateway_to_si_banking",
                name="API Gateway to SI Banking Operations",
                description="Route API Gateway banking operations to SI banking services",
                source_pattern="api_gateway",
                target_pattern="banking_integration",
                message_pattern="banking_*",
                source_role=ServiceRole.CORE,
                target_role=ServiceRole.SYSTEM_INTEGRATOR,
                strategy=RoutingStrategy.PRIORITY,
                priority=0,  # Highest priority
                conditions={
                    "operation_patterns": [
                        "create_mono_widget_link",
                        "process_mono_callback", 
                        "list_open_banking_connections",
                        "create_open_banking_connection",
                        "get_open_banking_connection",
                        "update_open_banking_connection",
                        "delete_open_banking_connection",
                        "get_banking_transactions",
                        "sync_banking_transactions",
                        "get_banking_accounts",
                        "get_account_balance",
                        "test_banking_connection",
                        "get_banking_connection_health",
                        "get_banking_statistics"
                    ]
                }
            ),
            
            # API Gateway to SI General Operations
            RoutingRule(
                rule_id="api_gateway_to_si_general",
                name="API Gateway to SI General Operations", 
                description="Route API Gateway operations to SI services",
                source_pattern="api_gateway",
                target_pattern="*",
                message_pattern="*",
                source_role=ServiceRole.CORE,
                target_role=ServiceRole.SYSTEM_INTEGRATOR,
                strategy=RoutingStrategy.LOAD_BALANCED,
                priority=1
            ),
            
            # SI to APP communication
            RoutingRule(
                rule_id="si_to_app_communication",
                name="SI to APP Communication",
                description="Route SI operations to APP services",
                source_pattern="*",
                target_pattern="*", 
                message_pattern="*",
                source_role=ServiceRole.SYSTEM_INTEGRATOR,
                target_role=ServiceRole.ACCESS_POINT_PROVIDER,
                strategy=RoutingStrategy.LOAD_BALANCED,
                priority=1
            ),
            
            # APP to SI communication
            RoutingRule(
                rule_id="app_to_si_communication",
                name="APP to SI Communication",
                description="Route APP responses to SI services",
                source_pattern="*",
                target_pattern="*",
                message_pattern="*", 
                source_role=ServiceRole.ACCESS_POINT_PROVIDER,
                target_role=ServiceRole.SYSTEM_INTEGRATOR,
                strategy=RoutingStrategy.BROADCAST,
                priority=1
            ),
            
            # Hybrid service coordination
            RoutingRule(
                rule_id="hybrid_service_coordination",
                name="Hybrid Service Coordination",
                description="Route hybrid coordinator operations",
                source_pattern="*",
                target_pattern="*",
                message_pattern="*",
                source_role=ServiceRole.HYBRID_COORDINATOR,
                target_role=ServiceRole.HYBRID,
                strategy=RoutingStrategy.ROUND_ROBIN,
                priority=2
            ),
            
            # Core platform alerts
            RoutingRule(
                rule_id="core_platform_alerts",
                name="Core Platform Alerts",
                description="Broadcast core platform alerts",
                source_pattern="*",
                target_pattern="*", 
                message_pattern="alert_*",
                source_role=ServiceRole.CORE,
                target_role=None,  # Broadcast to all
                strategy=RoutingStrategy.BROADCAST,
                priority=3
            )
        ]
        
        for rule in default_rules:
            await self.add_routing_rule(rule)
    
    async def shutdown(self):
        """Graceful shutdown of the Redis message router"""
        logger.info(f"Shutting down Redis Message Router - Instance: {self.instance_id}")
        
        try:
            # Cancel background tasks
            if self._maintenance_task:
                self._maintenance_task.cancel()
            if self._health_check_task:
                self._health_check_task.cancel()
            
            # Update instance status
            await self.redis.hset(
                f"{self.instances_key}:{self.instance_id}",
                "status",
                "shutdown"
            )
            
            # Close Redis connection
            await self.redis.close()
            
            logger.info("Redis Message Router shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def get_redis_message_router(redis_client: Optional[redis.Redis] = None,
                           event_bus: Optional[EventBus] = None,
                           instance_id: Optional[str] = None) -> RedisMessageRouter:
    """Factory function to create Redis-backed message router"""
    return RedisMessageRouter(redis_client, event_bus, instance_id)