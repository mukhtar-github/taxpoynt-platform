"""
TaxPoynt Core Platform
=====================
Core platform services for the TaxPoynt e-invoice platform.

This package provides:
- Authentication and authorization services
- Data management and database abstraction
- Message routing and event handling
- Monitoring and observability
- Security and compliance
- Transaction processing
- Regulatory compliance systems
"""

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"

# Core platform components
from . import authentication
from . import data_management
from . import messaging
from . import monitoring
from . import security

# Commonly used imports
from .events import EventBus, get_event_bus
from .notifications import NotificationService, get_notification_service
from .ai import AIService, get_ai_service
from .cache import CacheService, get_cache_service
from .storage import FileStorage, get_file_storage

__all__ = [
    'authentication',
    'data_management', 
    'messaging',
    'monitoring',
    'security',
    'EventBus',
    'get_event_bus',
    'NotificationService',
    'get_notification_service',
    'AIService',
    'get_ai_service',
    'CacheService',
    'get_cache_service',
    'FileStorage',
    'get_file_storage'
]