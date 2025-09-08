"""
Core Platform Cache Service
============================
Unified cache service interface for the core platform.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from uuid import UUID
import logging

from .data_management.cache_manager import (
    CacheManager, 
    CacheConfig, 
    CacheStrategy,
    SerializationFormat,
    get_cache_manager,
    initialize_cache_manager
)

logger = logging.getLogger(__name__)


class CacheService:
    """
    Unified cache service for core platform components.
    
    Provides a simplified interface over the enterprise cache manager
    for consistent usage across all platform services.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        """
        Initialize cache service.
        
        Args:
            cache_manager: Optional cache manager instance
        """
        self._cache_manager = cache_manager or get_cache_manager()
        
        if self._cache_manager is None:
            # Initialize with default configuration
            default_config = CacheConfig(
                default_ttl_seconds=3600,  # 1 hour
                max_memory_cache_size=1000,
                enable_compression=True,
                serialization_format=SerializationFormat.JSON,
                cache_strategy=CacheStrategy.WRITE_THROUGH,
                enable_metrics=True
            )
            self._cache_manager = initialize_cache_manager(default_config)
            logger.info("Initialized cache service with default configuration")
    
    async def initialize(self) -> bool:
        """
        Initialize the cache service asynchronously.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            if self._cache_manager is None:
                # Initialize with default configuration
                default_config = CacheConfig(
                    default_ttl_seconds=3600,  # 1 hour
                    max_memory_cache_size=1000,
                    enable_compression=True,
                    serialization_format=SerializationFormat.JSON,
                    cache_strategy=CacheStrategy.WRITE_THROUGH,
                    enable_metrics=True
                )
                self._cache_manager = initialize_cache_manager(default_config)
                logger.info("Cache service initialized asynchronously")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize cache service: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        if self._cache_manager is None:
            return default
        return self._cache_manager.get(key, default)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if self._cache_manager is None:
            return False
        return self._cache_manager.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self._cache_manager is None:
            return False
        return self._cache_manager.delete(key)
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """
        Get value from cache or set using factory function.
        
        Args:
            key: Cache key
            factory: Function to generate value if not in cache
            ttl: Time to live in seconds
            
        Returns:
            Cached or generated value
        """
        if self._cache_manager is None:
            return factory()
        return self._cache_manager.get_or_set(key, factory, ttl)
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment
            ttl: Time to live for new keys
            
        Returns:
            New value after increment
        """
        if self._cache_manager is None:
            return amount
        return self._cache_manager.increment(key, amount, ttl)
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        if self._cache_manager is None:
            return {}
        return self._cache_manager.get_many(keys)
    
    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            data: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if self._cache_manager is None:
            return False
        return self._cache_manager.set_many(data, ttl)
    
    def clear_tenant_cache(self, tenant_id: Union[str, UUID]):
        """
        Clear all cache entries for a specific tenant.
        
        Args:
            tenant_id: Tenant ID to clear cache for
        """
        if self._cache_manager is None:
            return
        
        if isinstance(tenant_id, str):
            tenant_id = UUID(tenant_id)
        
        self._cache_manager.clear_tenant_cache(tenant_id)
    
    def set_tenant_context(self, tenant_id: Union[str, UUID], organization_id: Union[str, UUID]):
        """
        Set tenant context for cache operations.
        
        Args:
            tenant_id: Tenant ID
            organization_id: Organization ID
        """
        if self._cache_manager is None:
            return
        
        if isinstance(tenant_id, str):
            tenant_id = UUID(tenant_id)
        if isinstance(organization_id, str):
            organization_id = UUID(organization_id)
        
        self._cache_manager.set_tenant_context(tenant_id, organization_id)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform cache health check.
        
        Returns:
            Health status dictionary
        """
        if self._cache_manager is None:
            return {"status": "unavailable", "error": "Cache manager not initialized"}
        return self._cache_manager.health_check()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics.
        
        Returns:
            Metrics dictionary
        """
        if self._cache_manager is None:
            return {"status": "unavailable"}
        
        metrics = self._cache_manager.get_metrics()
        return {
            "hits": metrics.hits,
            "misses": metrics.misses,
            "writes": metrics.writes,
            "deletes": metrics.deletes,
            "errors": metrics.errors,
            "total_operations": metrics.total_operations,
            "hit_ratio": metrics.hit_ratio,
            "avg_response_time_ms": metrics.avg_response_time_ms,
            "memory_usage_mb": metrics.memory_usage_mb,
            "redis_memory_usage_mb": metrics.redis_memory_usage_mb,
            "last_reset": metrics.last_reset
        }
    
    def reset_metrics(self):
        """Reset cache metrics."""
        if self._cache_manager is not None:
            self._cache_manager.reset_metrics()


# Global cache service instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get global cache service instance.
    
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def initialize_cache_service(cache_manager: Optional[CacheManager] = None) -> CacheService:
    """
    Initialize global cache service.
    
    Args:
        cache_manager: Optional cache manager instance
        
    Returns:
        CacheService instance
    """
    global _cache_service
    _cache_service = CacheService(cache_manager)
    return _cache_service


# Export commonly used class for direct import
CacheService = CacheService