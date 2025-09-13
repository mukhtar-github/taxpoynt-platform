"""
Unified RBAC - Hybrid Services
==============================

Unified role-based access control across SI, APP, and Hybrid services.
Integrates with existing access_middleware and subscription_guard.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .access_middleware import AccessMiddleware
from .subscription_guard import SubscriptionGuard

logger = logging.getLogger(__name__)


class UnifiedRBAC:
    """
    Unified role-based access control that integrates existing access components.
    Manages permissions across SI, APP, and Hybrid services uniformly.
    """
    
    def __init__(self):
        self.access_middleware = AccessMiddleware()
        self.subscription_guard = SubscriptionGuard()
        
        # Default role definitions
        self.roles = {
            'admin': {
                'permissions': ['*'],  # All permissions
                'services': ['*']
            },
            'si_user': {
                'permissions': ['read_integrations', 'write_integrations', 'read_banking'],
                'services': ['si_services', 'hybrid_services']
            },
            'app_user': {
                'permissions': ['read_invoices', 'write_invoices', 'read_compliance'],
                'services': ['app_services', 'hybrid_services']
            }
        }
        self.user_roles: Dict[str, List[str]] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize unified RBAC components"""
        if self.is_initialized:
            return
            
        logger.info("Initializing Unified RBAC")
        
        # Initialize components
        await self.access_middleware.initialize()
        await self.subscription_guard.initialize()
        
        self.is_initialized = True
        logger.info("Unified RBAC initialized successfully")
    
    async def check_permission(self, user_id: str, permission: str, service: str) -> bool:
        """Check if user has permission for a specific service operation"""
        if not self.is_initialized:
            await self.initialize()
            
        # First check subscription-level access
        subscription_access = await self.subscription_guard.check_service_access(
            user_id, service
        )
        if not subscription_access:
            return False
            
        # Then check middleware-level access
        middleware_access = await self.access_middleware.check_access_permission(
            user_id, permission, service
        )
        if not middleware_access:
            return False
            
        # Finally check role-based permissions
        user_roles = self.user_roles.get(user_id, [])
        
        for role in user_roles:
            role_config = self.roles.get(role, {})
            
            # Check if role has wildcard permissions
            if '*' in role_config.get('permissions', []):
                return True
                
            # Check specific permission
            if permission in role_config.get('permissions', []):
                # Check if role can access this service
                if '*' in role_config.get('services', []) or service in role_config.get('services', []):
                    return True
                    
        return False
    
    async def assign_role(self, user_id: str, role: str) -> bool:
        """Assign role to user"""
        if role not in self.roles:
            return False
            
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
            
        if role not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role)
            
        # Update access middleware with new role
        await self.access_middleware.update_user_permissions(user_id, self.roles[role])
        
        return True
    
    async def revoke_role(self, user_id: str, role: str) -> bool:
        """Revoke role from user"""
        if user_id not in self.user_roles or role not in self.user_roles[user_id]:
            return False
            
        self.user_roles[user_id].remove(role)
        if not self.user_roles[user_id]:
            del self.user_roles[user_id]
            
        # Update access middleware
        remaining_permissions = []
        for remaining_role in self.user_roles.get(user_id, []):
            remaining_permissions.extend(self.roles.get(remaining_role, {}).get('permissions', []))
        
        await self.access_middleware.update_user_permissions(user_id, {'permissions': remaining_permissions})
        
        return True
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get all permissions for a user"""
        if not self.is_initialized:
            await self.initialize()
            
        user_roles = self.user_roles.get(user_id, [])
        permissions = set()
        
        for role in user_roles:
            role_config = self.roles.get(role, {})
            role_permissions = role_config.get('permissions', [])
            
            if '*' in role_permissions:
                return ['*']  # All permissions
                
            permissions.update(role_permissions)
            
        return list(permissions)
    
    async def get_accessible_services(self, user_id: str) -> List[str]:
        """Get list of services user can access"""
        if not self.is_initialized:
            await self.initialize()
            
        # Get subscription-level accessible services
        subscription_services = await self.subscription_guard.get_accessible_services(user_id)
        
        # Get role-based accessible services
        user_roles = self.user_roles.get(user_id, [])
        role_services = set()
        
        for role in user_roles:
            role_config = self.roles.get(role, {})
            services = role_config.get('services', [])
            
            if '*' in services:
                return subscription_services  # Return all subscription services if wildcard
                
            role_services.update(services)
        
        # Intersection of subscription and role services
        return list(set(subscription_services) & role_services)
    
    async def check_service_access(self, user_id: str, service: str) -> Dict[str, Any]:
        """Comprehensive service access check"""
        if not self.is_initialized:
            await self.initialize()
            
        # Check subscription
        subscription_check = await self.subscription_guard.check_service_access(user_id, service)
        
        # Check middleware  
        middleware_check = await self.access_middleware.check_service_access(user_id, service)
        
        # Check roles
        accessible_services = await self.get_accessible_services(user_id)
        role_check = service in accessible_services
        
        overall_access = subscription_check and middleware_check and role_check
        
        return {
            'user_id': user_id,
            'service': service,
            'access_granted': overall_access,
            'checks': {
                'subscription': subscription_check,
                'middleware': middleware_check,
                'roles': role_check
            },
            'user_roles': self.user_roles.get(user_id, []),
            'timestamp': datetime.now().isoformat()
        }
    
    async def get_rbac_summary(self) -> Dict[str, Any]:
        """Get RBAC system summary"""
        if not self.is_initialized:
            await self.initialize()
            
        return {
            'access_middleware_status': await self.access_middleware.get_status(),
            'subscription_guard_status': await self.subscription_guard.get_status(),
            'total_users': len(self.user_roles),
            'total_roles': len(self.roles),
            'role_assignments': {role: len([u for u, roles in self.user_roles.items() if role in roles]) 
                               for role in self.roles.keys()},
            'timestamp': datetime.now().isoformat()
        }