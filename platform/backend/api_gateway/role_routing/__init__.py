"""
API Gateway Role-Based Routing System
====================================
Provides HTTP-level role-aware request routing that integrates with the existing
message router and role management systems.

This module extends the existing message routing capabilities with:
- HTTP request role detection and context analysis
- FastAPI-specific role-based endpoint routing
- Integration with existing core_platform/authentication/role_manager
- Bridging HTTP requests to internal message routing system
- API endpoint protection and permission enforcement

Integration Points:
- Uses core_platform.authentication.role_manager for role validation
- Integrates with core_platform.messaging.message_router for internal routing
- Leverages existing hybrid_services for cross-role operations

Components:
- models.py: HTTP-specific routing models that extend existing role models
- role_detector.py: HTTP request analysis and role context detection
- permission_guard.py: FastAPI middleware for role-based endpoint protection  
- si_router.py: FastAPI router for SI-specific HTTP endpoints
- app_router.py: FastAPI router for APP-specific HTTP endpoints
- hybrid_router.py: FastAPI router for cross-role HTTP endpoints
"""

# Import from NEW architecture core components
# Fix relative import issues by using absolute imports
import sys
from pathlib import Path

# Add the platform backend to the path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from core_platform.authentication.role_manager import PlatformRole, RoleScope
    from core_platform.messaging.message_router import ServiceRole, MessageRouter
except ImportError:
    # Fallback for development - create minimal classes
    from enum import Enum
    
    class PlatformRole(Enum):
        SYSTEM_INTEGRATOR = "system_integrator"
        ACCESS_POINT_PROVIDER = "access_point_provider"
        HYBRID = "hybrid"
        PLATFORM_ADMIN = "platform_admin"
        TENANT_ADMIN = "tenant_admin"
        USER = "user"
    
    class RoleScope(Enum):
        GLOBAL = "global"
        TENANT = "tenant"
        SERVICE = "service"
        ENVIRONMENT = "environment"
    
    class ServiceRole(Enum):
        SYSTEM_INTEGRATOR = "si"
        ACCESS_POINT_PROVIDER = "app"
        HYBRID = "hybrid"
        CORE = "core"
    
    class MessageRouter:
        def __init__(self):
            pass
            
        async def route_message(self, service_role, operation, payload):
            """Fallback route_message method"""
            return {"status": "success", "message": f"Mock response for {operation}", "data": payload}

from .models import (
    HTTPRoutingContext, APIEndpointRule, RoleBasedRoute,
    RequestAnalysis, RoutePermission
)
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard
from .si_router import SIServicesRouter
from .app_router import APPServicesRouter  
from .hybrid_router import HybridServicesRouter
from .admin_router import create_admin_router

__all__ = [
    # Existing integrations
    'PlatformRole',
    'RoleScope', 
    'ServiceRole',
    'MessageRouter',
    
    # New HTTP-specific components
    'HTTPRoutingContext',
    'APIEndpointRule',
    'RoleBasedRoute',
    'RequestAnalysis',
    'RoutePermission',
    'HTTPRoleDetector',
    'APIPermissionGuard',
    'SIAPIRouter',
    'APPAPIRouter',
    'HybridAPIRouter',
    'create_admin_router'
]