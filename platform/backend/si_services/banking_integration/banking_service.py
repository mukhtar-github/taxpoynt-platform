"""
SI Banking Service
==================

Main service for handling banking-related operations for System Integrators.
Acts as a dispatcher to specific banking provider services.

Operations Handled:
- create_mono_widget_link
- list_open_banking_connections  
- create_open_banking_connection
- get_open_banking_connection
- update_open_banking_connection
- delete_open_banking_connection
- get_banking_transactions
- sync_banking_transactions
- get_banking_accounts
- get_account_balance
- test_banking_connection
- get_banking_connection_health

Architecture:
- Follows SI service patterns
- Delegates to provider-specific services
- Handles message router operations
"""

import logging
from typing import Dict, Any, Optional

from .mono_integration_service import MonoIntegrationService

logger = logging.getLogger(__name__)


class SIBankingService:
    """
    Main banking service for System Integrators.
    
    Handles all banking-related operations and delegates to appropriate
    provider-specific services.
    """
    
    def __init__(self):
        """Initialize banking service"""
        self.mono_service = MonoIntegrationService()
        
    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle banking operation from message router.
        
        Args:
            operation: Operation name
            payload: Operation payload
            
        Returns:
            Dict with operation result
        """
        try:
            logger.info(f"Handling banking operation: {operation}")
            
            # Extract common parameters
            si_id = payload.get("si_id")
            api_version = payload.get("api_version", "v1")
            
            if not si_id:
                raise ValueError("SI ID is required for banking operations")
            
            # Route to appropriate handler
            if operation == "create_mono_widget_link":
                return await self._handle_create_mono_widget_link(si_id, payload)
            elif operation == "list_open_banking_connections":
                return await self._handle_list_open_banking_connections(si_id, payload)
            elif operation == "create_open_banking_connection":
                return await self._handle_create_open_banking_connection(si_id, payload)
            elif operation == "get_open_banking_connection":
                return await self._handle_get_open_banking_connection(si_id, payload)
            elif operation == "update_open_banking_connection":
                return await self._handle_update_open_banking_connection(si_id, payload)
            elif operation == "delete_open_banking_connection":
                return await self._handle_delete_open_banking_connection(si_id, payload)
            elif operation == "get_banking_transactions":
                return await self._handle_get_banking_transactions(si_id, payload)
            elif operation == "sync_banking_transactions":
                return await self._handle_sync_banking_transactions(si_id, payload)
            elif operation == "get_banking_accounts":
                return await self._handle_get_banking_accounts(si_id, payload)
            elif operation == "get_account_balance":
                return await self._handle_get_account_balance(si_id, payload)
            elif operation == "test_banking_connection":
                return await self._handle_test_banking_connection(si_id, payload)
            elif operation == "get_banking_connection_health":
                return await self._handle_get_banking_connection_health(si_id, payload)
            else:
                raise ValueError(f"Unknown banking operation: {operation}")
                
        except Exception as e:
            logger.error(f"Error handling banking operation {operation}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Banking operation failed: {str(e)}")
    
    async def _handle_create_mono_widget_link(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Mono widget link creation"""
        widget_config = payload.get("widget_config")
        if not widget_config:
            raise ValueError("Widget config is required")
            
        result = await self.mono_service.create_mono_widget_link(si_id, widget_config)
        
        return {
            "operation": "create_mono_widget_link",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_list_open_banking_connections(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle listing Open Banking connections"""
        filters = payload.get("filters", {})
        
        result = await self.mono_service.list_open_banking_connections(si_id, filters)
        
        return {
            "operation": "list_open_banking_connections",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_create_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle creating Open Banking connection"""
        connection_data = payload.get("connection_data")
        if not connection_data:
            raise ValueError("Connection data is required")
            
        result = await self.mono_service.create_open_banking_connection(si_id, connection_data)
        
        return {
            "operation": "create_open_banking_connection",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_get_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting Open Banking connection"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
            
        # For now, return mock data
        result = {
            "connection_id": connection_id,
            "provider": "mono",
            "status": "active",
            "si_id": si_id
        }
        
        return {
            "operation": "get_open_banking_connection",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_update_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle updating Open Banking connection"""
        connection_id = payload.get("connection_id")
        updates = payload.get("updates", {})
        
        if not connection_id:
            raise ValueError("Connection ID is required")
            
        # For now, return mock data
        result = {
            "connection_id": connection_id,
            "updates_applied": updates,
            "si_id": si_id
        }
        
        return {
            "operation": "update_open_banking_connection",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_delete_open_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle deleting Open Banking connection"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
            
        # For now, return mock data
        result = {
            "connection_id": connection_id,
            "deleted": True,
            "si_id": si_id
        }
        
        return {
            "operation": "delete_open_banking_connection",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_get_banking_transactions(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting banking transactions"""
        filters = payload.get("filters", {})
        
        result = await self.mono_service.get_banking_transactions(si_id, filters)
        
        return {
            "operation": "get_banking_transactions",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_sync_banking_transactions(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle syncing banking transactions"""
        sync_config = payload.get("sync_config", {})
        
        # For now, return mock sync result
        result = {
            "sync_started": True,
            "config": sync_config,
            "estimated_duration": "5-10 minutes",
            "si_id": si_id
        }
        
        return {
            "operation": "sync_banking_transactions",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_get_banking_accounts(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting banking accounts"""
        filters = payload.get("filters", {})
        
        result = await self.mono_service.get_banking_accounts(si_id, filters)
        
        return {
            "operation": "get_banking_accounts",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_get_account_balance(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting account balance"""
        account_id = payload.get("account_id")
        if not account_id:
            raise ValueError("Account ID is required")
            
        # For now, return mock balance
        result = {
            "account_id": account_id,
            "balance": 1500000.00,  # 1.5M NGN
            "currency": "NGN",
            "last_updated": "2024-12-31T00:00:00Z",
            "si_id": si_id
        }
        
        return {
            "operation": "get_account_balance",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_test_banking_connection(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle testing banking connection"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
            
        result = await self.mono_service.test_banking_connection(si_id, connection_id)
        
        return {
            "operation": "test_banking_connection",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def _handle_get_banking_connection_health(self, si_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle getting banking connection health"""
        connection_id = payload.get("connection_id")
        if not connection_id:
            raise ValueError("Connection ID is required")
            
        # For now, return mock health data
        result = {
            "connection_id": connection_id,
            "status": "healthy",
            "last_check": "2024-12-31T00:00:00Z",
            "uptime": "99.9%",
            "response_time": "150ms",
            "si_id": si_id
        }
        
        return {
            "operation": "get_banking_connection_health",
            "success": True,
            "data": result,
            "si_id": si_id
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on banking service"""
        try:
            mono_health = await self.mono_service.health_check()
            
            return {
                "status": "healthy",
                "services": {
                    "mono": mono_health
                }
            }
            
        except Exception as e:
            logger.error(f"Banking service health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.mono_service.cleanup()