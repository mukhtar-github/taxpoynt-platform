"""
Core Platform Base Service
==========================
Base service class providing common functionality for all platform services.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .exceptions import ServiceError, ConfigurationError


@dataclass
class ServiceConfig:
    """Base service configuration"""
    service_name: str
    service_version: str = "1.0.0"
    environment: str = "production"
    log_level: str = "INFO"
    health_check_interval: int = 60  # seconds
    metrics_enabled: bool = True
    config_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceMetrics:
    """Service metrics tracking"""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_health_check: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


class BaseService(ABC):
    """
    Base service class for all TaxPoynt platform services
    
    Provides common functionality including:
    - Service lifecycle management  
    - Health checking
    - Metrics collection
    - Configuration management
    - Logging setup
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize base service"""
        self._config_dict = config or {}
        self._service_config = self._create_service_config()
        self._logger = self._setup_logging()
        self._metrics = ServiceMetrics()
        self._is_running = False
        self._background_tasks: List[asyncio.Task] = []
        self._health_status = "initializing"
        self._startup_time: Optional[datetime] = None
        
        # Service-specific initialization
        self._initialize_service()
    
    def _create_service_config(self) -> ServiceConfig:
        """Create service configuration from provided config dict"""
        return ServiceConfig(
            service_name=self._config_dict.get('service_name', self.__class__.__name__),
            service_version=self._config_dict.get('service_version', '1.0.0'),
            environment=self._config_dict.get('environment', 'production'),
            log_level=self._config_dict.get('log_level', 'INFO'),
            health_check_interval=self._config_dict.get('health_check_interval', 60),
            metrics_enabled=self._config_dict.get('metrics_enabled', True),
            config_data=self._config_dict.get('config_data', {})
        )
    
    def _setup_logging(self) -> logging.Logger:
        """Setup service logging"""
        logger = logging.getLogger(self._service_config.service_name)
        logger.setLevel(getattr(logging, self._service_config.log_level.upper()))
        
        # Avoid duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self._service_config.service_name} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_service(self) -> None:
        """Service-specific initialization - override in subclasses"""
        pass
    
    @property
    def config(self) -> ServiceConfig:
        """Get service configuration"""
        return self._service_config
    
    @property
    def logger(self) -> logging.Logger:
        """Get service logger"""
        return self._logger
    
    @property 
    def metrics(self) -> ServiceMetrics:
        """Get service metrics"""
        return self._metrics
    
    @property
    def is_running(self) -> bool:
        """Check if service is running"""
        return self._is_running
    
    @property
    def health_status(self) -> str:
        """Get current health status"""
        return self._health_status
    
    async def start(self) -> None:
        """Start the service"""
        try:
            self._logger.info(f"Starting {self._service_config.service_name}")
            self._startup_time = datetime.now(timezone.utc)
            self._health_status = "starting"
            
            # Service-specific startup
            await self.initialize()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self._is_running = True
            self._health_status = "healthy"
            self._logger.info(f"{self._service_config.service_name} started successfully")
            
        except Exception as e:
            self._health_status = "failed"
            self._logger.error(f"Failed to start {self._service_config.service_name}: {str(e)}")
            raise ServiceError(f"Service startup failed: {str(e)}")
    
    async def stop(self) -> None:
        """Stop the service"""
        try:
            self._logger.info(f"Stopping {self._service_config.service_name}")
            self._health_status = "stopping"
            
            # Cancel background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)
            
            # Service-specific cleanup
            await self.cleanup()
            
            self._is_running = False
            self._health_status = "stopped"
            self._logger.info(f"{self._service_config.service_name} stopped")
            
        except Exception as e:
            self._health_status = "error"
            self._logger.error(f"Error stopping {self._service_config.service_name}: {str(e)}")
            raise ServiceError(f"Service shutdown failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            self._metrics.last_health_check = datetime.now(timezone.utc)
            
            # Service-specific health check
            service_health = await self.check_health()
            
            # Calculate uptime
            uptime_seconds = 0
            if self._startup_time:
                uptime_seconds = (datetime.now(timezone.utc) - self._startup_time).total_seconds()
            
            # Basic health info
            health_info = {
                'service': self._service_config.service_name,
                'version': self._service_config.service_version,
                'status': self._health_status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'uptime_seconds': uptime_seconds,
                'is_running': self._is_running,
                'environment': self._service_config.environment
            }
            
            # Add service-specific health info
            if service_health:
                health_info.update(service_health)
            
            # Add metrics if enabled
            if self._service_config.metrics_enabled:
                health_info['metrics'] = {
                    'total_requests': self._metrics.total_requests,
                    'successful_requests': self._metrics.successful_requests, 
                    'failed_requests': self._metrics.failed_requests,
                    'error_rate': self._metrics.error_rate,
                    'avg_response_time': self._metrics.avg_response_time,
                    'custom_metrics': self._metrics.custom_metrics
                }
            
            return health_info
            
        except Exception as e:
            self._logger.error(f"Health check failed: {str(e)}")
            return {
                'service': self._service_config.service_name,
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def update_metrics(self, success: bool, response_time: float = 0.0) -> None:
        """Update service metrics"""
        if not self._service_config.metrics_enabled:
            return
            
        self._metrics.total_requests += 1
        
        if success:
            self._metrics.successful_requests += 1
        else:
            self._metrics.failed_requests += 1
        
        # Update error rate
        if self._metrics.total_requests > 0:
            self._metrics.error_rate = self._metrics.failed_requests / self._metrics.total_requests
        
        # Update average response time
        if response_time > 0:
            current_avg = self._metrics.avg_response_time
            total_requests = self._metrics.total_requests
            self._metrics.avg_response_time = ((current_avg * (total_requests - 1)) + response_time) / total_requests
    
    def add_custom_metric(self, key: str, value: Any) -> None:
        """Add custom metric"""
        if self._service_config.metrics_enabled:
            self._metrics.custom_metrics[key] = value
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks"""
        # Health check task
        if self._service_config.health_check_interval > 0:
            health_task = asyncio.create_task(self._health_check_worker())
            self._background_tasks.append(health_task)
        
        # Service-specific background tasks
        service_tasks = await self.get_background_tasks()
        if service_tasks:
            self._background_tasks.extend(service_tasks)
    
    async def _health_check_worker(self) -> None:
        """Background health check worker"""
        while self._is_running:
            try:
                await asyncio.sleep(self._service_config.health_check_interval)
                await self.health_check()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Health check worker error: {str(e)}")
                await asyncio.sleep(5)  # Short delay on error
    
    # Abstract methods for subclasses to implement
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize service - implement in subclass"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup service resources - implement in subclass"""
        pass
    
    async def check_health(self) -> Optional[Dict[str, Any]]:
        """Service-specific health check - override in subclass"""
        return None
    
    async def get_background_tasks(self) -> Optional[List[asyncio.Task]]:
        """Get service-specific background tasks - override in subclass"""
        return None