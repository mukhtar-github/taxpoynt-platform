"""
Dynamic Config Manager - Hybrid Services
========================================

Dynamic configuration management across all platform services.
Integrates with existing config_coordinator and environment_manager.
"""

import asyncio
import logging
from typing import Dict, Any, Union, List
from datetime import datetime

from .config_coordinator import ConfigCoordinator
from .environment_manager import EnvironmentManager

logger = logging.getLogger(__name__)


class DynamicConfigManager:
    """
    Dynamic configuration management that integrates with existing components.
    Provides real-time configuration updates across all services.
    """
    
    def __init__(self):
        self.config_coordinator = ConfigCoordinator()
        self.environment_manager = EnvironmentManager()
        self.config_watchers: Dict[str, List[callable]] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize dynamic configuration components"""
        if self.is_initialized:
            return
            
        logger.info("Initializing Dynamic Config Manager")
        
        # Initialize underlying components
        await self.config_coordinator.initialize()
        await self.environment_manager.initialize()
        
        self.is_initialized = True
        logger.info("Dynamic Config Manager initialized successfully")
    
    async def get_config(self, service: str, key: str = None) -> Union[Dict[str, Any], Any]:
        """Get configuration for a service using existing coordinator"""
        if not self.is_initialized:
            await self.initialize()
            
        # Use existing config coordinator
        if key:
            return await self.config_coordinator.get_service_config(service, key)
        else:
            return await self.config_coordinator.get_all_service_configs(service)
    
    async def set_config(self, service: str, key: str, value: Any) -> bool:
        """Set configuration for a service"""
        if not self.is_initialized:
            await self.initialize()
            
        # Use existing config coordinator to update config
        success = await self.config_coordinator.update_service_config(
            service, {key: value}
        )
        
        if success:
            # Notify watchers
            await self._notify_watchers(service, key, value)
            
        return success
    
    async def watch_config(self, service: str, key: str, callback: callable):
        """Watch for configuration changes"""
        watcher_key = f"{service}.{key}"
        if watcher_key not in self.config_watchers:
            self.config_watchers[watcher_key] = []
        self.config_watchers[watcher_key].append(callback)
        
    async def _notify_watchers(self, service: str, key: str, value: Any):
        """Notify configuration watchers of changes"""
        watcher_key = f"{service}.{key}"
        if watcher_key in self.config_watchers:
            for watcher in self.config_watchers[watcher_key]:
                try:
                    if asyncio.iscoroutinefunction(watcher):
                        await watcher(service, key, value)
                    else:
                        watcher(service, key, value)
                except Exception as e:
                    logger.error(f"Error notifying config watcher: {e}")
    
    async def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration"""
        if not self.is_initialized:
            await self.initialize()
            
        return await self.environment_manager.get_current_environment_config()
    
    async def reload_configuration(self, service: str = None) -> bool:
        """Reload configuration from source"""
        if not self.is_initialized:
            await self.initialize()
            
        if service:
            return await self.config_coordinator.reload_service_configuration(service)
        else:
            return await self.config_coordinator.reload_all_configurations()
    
    async def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration management summary"""
        if not self.is_initialized:
            await self.initialize()
            
        return {
            'config_coordinator_status': await self.config_coordinator.get_status(),
            'environment_manager_status': await self.environment_manager.get_status(),
            'active_watchers': len(self.config_watchers),
            'timestamp': datetime.now().isoformat()
        }