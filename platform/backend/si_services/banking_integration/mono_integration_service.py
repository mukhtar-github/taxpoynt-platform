"""
Mono Integration Service for System Integrators
===============================================

Handles Mono Open Banking integration for System Integrator operations.
Provides a service layer between the API endpoints and the Mono connector.

Key Features:
- Widget link generation
- Account linking management
- Transaction processing for e-invoicing
- Business account setup
- Webhook handling

Architecture:
- Integrates with existing MonoConnector
- Follows SI service patterns
- Message router operation handler
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from external_integrations.financial_systems.banking.open_banking.providers.mono.connector import (
    MonoConnector, 
    MonoConfig,
    AccountLinkingSession
)
from external_integrations.financial_systems.banking.open_banking.providers.mono.exceptions import (
    MonoBaseException,
    MonoAuthenticationError,
    MonoConnectionError,
    MonoValidationError
)

logger = logging.getLogger(__name__)


class MonoIntegrationService:
    """
    Service layer for Mono Open Banking integration.
    
    Handles SI-specific operations and integrates with the sophisticated
    MonoConnector infrastructure.
    """
    
    def __init__(self):
        """Initialize Mono integration service"""
        self.mono_connector: Optional[MonoConnector] = None
        self._config = self._load_config()
        
    def _load_config(self) -> MonoConfig:
        """Load Mono configuration from environment"""
        return MonoConfig(
            secret_key=os.getenv("MONO_SECRET_KEY", "test_sk_qhztoaaq7hzcbew22tap"),
            app_id=os.getenv("MONO_APP_ID", "app_test_sandbox_taxpoynt"),
            environment=os.getenv("MONO_ENVIRONMENT", "sandbox"),
            public_key=os.getenv("MONO_PUBLIC_KEY"),
            webhook_url=os.getenv("MONO_WEBHOOK_URL"),
            webhook_secret=os.getenv("MONO_WEBHOOK_SECRET", "sec_O62WW0RY6TP8ZGOPNILU"),
            enable_webhook_verification=os.getenv("MONO_VERIFY_WEBHOOKS", "true").lower() == "true",
            auto_invoice_generation=os.getenv("MONO_AUTO_INVOICE", "false").lower() == "true",
            invoice_min_amount=Decimal(os.getenv("MONO_MIN_INVOICE_AMOUNT", "1000")),
            max_concurrent_requests=int(os.getenv("MONO_MAX_CONCURRENT_REQUESTS", "3")),
            default_transaction_limit=int(os.getenv("MONO_DEFAULT_TRANSACTION_LIMIT", "50"))
        )
    
    async def get_connector(self) -> MonoConnector:
        """Get or create Mono connector instance"""
        if self.mono_connector is None:
            self.mono_connector = MonoConnector(self._config)
            await self.mono_connector.__aenter__()
        return self.mono_connector
    
    async def create_mono_widget_link(self, si_id: str, widget_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Mono widget link for account linking.
        
        Args:
            si_id: System Integrator ID
            widget_config: Widget configuration from API request
            
        Returns:
            Dict with mono_url and linking session details
        """
        try:
            logger.info(f"Creating Mono widget link for SI: {si_id}")
            
            # Extract configuration
            customer = widget_config["customer"]
            scope = widget_config.get("scope", "auth")
            redirect_url = widget_config["redirect_url"]
            meta_data = widget_config.get("meta", {})
            
            # Add SI context to metadata
            meta_data.update({
                "si_id": si_id,
                "platform": "taxpoynt",
                "integration_type": "si_banking"
            })
            
            # Get connector and initiate linking
            connector = await self.get_connector()
            
            session = await connector.initiate_account_linking(
                customer_name=customer["name"],
                customer_email=customer["email"],
                redirect_url=redirect_url,
                customer_id=customer.get("id"),
                reference=meta_data.get("ref"),
                metadata=meta_data
            )
            
            logger.info(f"Mono widget link created successfully: {session.session_id}")
            
            return {
                "session_id": session.session_id,
                "mono_url": session.mono_url,
                "reference": session.reference,
                "customer_name": session.customer_name,
                "customer_email": session.customer_email,
                "expires_at": session.expires_at.isoformat(),
                "status": session.status,
                "si_id": si_id
            }
            
        except MonoValidationError as e:
            logger.error(f"Mono validation error for SI {si_id}: {str(e)}")
            raise ValueError(f"Invalid widget configuration: {str(e)}")
            
        except MonoAuthenticationError as e:
            logger.error(f"Mono authentication error for SI {si_id}: {str(e)}")
            raise ConnectionError(f"Mono authentication failed: {str(e)}")
            
        except MonoConnectionError as e:
            logger.error(f"Mono connection error for SI {si_id}: {str(e)}")
            raise ConnectionError(f"Mono API connection failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error creating Mono widget link for SI {si_id}: {str(e)}", exc_info=True)
            raise RuntimeError(f"Widget link creation failed: {str(e)}")
    
    async def process_mono_callback(self, si_id: str, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Mono banking callback after user completes account linking.
        
        Args:
            si_id: System Integrator ID
            callback_data: Callback data from Mono
            
        Returns:
            Dict with processed callback results and linked accounts
        """
        try:
            logger.info(f"Processing Mono callback for SI: {si_id}")
            
            # Extract callback parameters
            auth_code = callback_data.get("code")
            state = callback_data.get("state")
            error = callback_data.get("error")
            
            # Handle error callbacks
            if error:
                logger.error(f"Mono callback error for SI {si_id}: {error}")
                return {
                    "success": False,
                    "error": error,
                    "message": f"Banking connection failed: {error}",
                    "si_id": si_id
                }
            
            # Validate required parameters
            if not auth_code:
                raise ValueError("Missing authorization code in callback")
            
            # Get connector and process the callback
            connector = await self.get_connector()
            
            # Exchange authorization code for account access
            account_linking_result = await connector.complete_account_linking(
                authorization_code=auth_code,
                state_parameter=state,
                si_id=si_id
            )
            
            logger.info(f"Mono account linking completed for SI {si_id}: {account_linking_result.account_id}")
            
            return {
                "success": True,
                "message": "Banking accounts successfully linked",
                "data": {
                    "account_id": account_linking_result.account_id,
                    "account_name": account_linking_result.account_name,
                    "bank_name": account_linking_result.bank_name,
                    "account_type": account_linking_result.account_type,
                    "linked_at": account_linking_result.linked_at.isoformat(),
                    "accounts": [account_linking_result.to_dict()],  # For frontend compatibility
                    "provider": "mono"
                },
                "si_id": si_id,
                "callback_processed_at": datetime.utcnow().isoformat()
            }
            
        except MonoValidationError as e:
            logger.error(f"Mono validation error in callback for SI {si_id}: {str(e)}")
            return {
                "success": False,
                "error": "validation_error",
                "message": f"Invalid callback data: {str(e)}",
                "si_id": si_id
            }
            
        except MonoAuthenticationError as e:
            logger.error(f"Mono authentication error in callback for SI {si_id}: {str(e)}")
            return {
                "success": False,
                "error": "authentication_error", 
                "message": f"Banking authentication failed: {str(e)}",
                "si_id": si_id
            }
            
        except MonoConnectionError as e:
            logger.error(f"Mono connection error in callback for SI {si_id}: {str(e)}")
            return {
                "success": False,
                "error": "connection_error",
                "message": f"Banking service connection failed: {str(e)}",
                "si_id": si_id
            }
            
        except Exception as e:
            logger.error(f"Unexpected error processing Mono callback for SI {si_id}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": "processing_error",
                "message": f"Callback processing failed: {str(e)}",
                "si_id": si_id
            }
    
    async def list_open_banking_connections(self, si_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        List Open Banking connections for a System Integrator.
        
        Args:
            si_id: System Integrator ID
            filters: Query filters
            
        Returns:
            Dict with connections list and metadata
        """
        try:
            logger.info(f"Listing Open Banking connections for SI: {si_id}")
            
            # For now, return mock data since we need to implement persistence
            # In a real implementation, you'd query a database of connections
            
            return {
                "connections": [],
                "total": 0,
                "filters_applied": filters,
                "si_id": si_id,
                "providers": ["mono", "stitch", "unified_banking"]
            }
            
        except Exception as e:
            logger.error(f"Error listing connections for SI {si_id}: {str(e)}")
            raise RuntimeError(f"Failed to list connections: {str(e)}")
    
    async def create_open_banking_connection(self, si_id: str, connection_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create Open Banking connection.
        
        Args:
            si_id: System Integrator ID
            connection_data: Connection configuration
            
        Returns:
            Dict with connection details
        """
        try:
            logger.info(f"Creating Open Banking connection for SI: {si_id}")
            
            provider = connection_data["provider"]
            org_id = connection_data["organization_id"]
            config = connection_data["connection_config"]
            
            # For now, return mock response
            # In a real implementation, you'd persist this and set up the connection
            
            connection_id = f"conn_{provider}_{si_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            return {
                "connection_id": connection_id,
                "provider": provider,
                "organization_id": org_id,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "si_id": si_id
            }
            
        except Exception as e:
            logger.error(f"Error creating connection for SI {si_id}: {str(e)}")
            raise RuntimeError(f"Failed to create connection: {str(e)}")
    
    async def get_banking_accounts(self, si_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get banking accounts for a System Integrator.
        
        Args:
            si_id: System Integrator ID
            filters: Query filters
            
        Returns:
            Dict with accounts list
        """
        try:
            logger.info(f"Getting banking accounts for SI: {si_id}")
            
            # Mock response - in real implementation, query connected accounts
            return {
                "accounts": [],
                "total": 0,
                "si_id": si_id,
                "filters_applied": filters
            }
            
        except Exception as e:
            logger.error(f"Error getting accounts for SI {si_id}: {str(e)}")
            raise RuntimeError(f"Failed to get accounts: {str(e)}")
    
    async def get_banking_transactions(self, si_id: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get banking transactions for a System Integrator.
        
        Args:
            si_id: System Integrator ID
            filters: Query filters
            
        Returns:
            Dict with transactions list
        """
        try:
            logger.info(f"Getting banking transactions for SI: {si_id}")
            
            # Mock response - in real implementation, fetch from connected accounts
            return {
                "transactions": [],
                "total": 0,
                "si_id": si_id,
                "filters_applied": filters
            }
            
        except Exception as e:
            logger.error(f"Error getting transactions for SI {si_id}: {str(e)}")
            raise RuntimeError(f"Failed to get transactions: {str(e)}")
    
    async def test_banking_connection(self, si_id: str, connection_id: str) -> Dict[str, Any]:
        """
        Test banking connection.
        
        Args:
            si_id: System Integrator ID
            connection_id: Connection identifier
            
        Returns:
            Dict with test results
        """
        try:
            logger.info(f"Testing banking connection {connection_id} for SI: {si_id}")
            
            # Mock response - in real implementation, test the actual connection
            return {
                "connection_id": connection_id,
                "status": "healthy",
                "test_time": datetime.utcnow().isoformat(),
                "api_connectivity": True,
                "authentication": True,
                "si_id": si_id
            }
            
        except Exception as e:
            logger.error(f"Error testing connection {connection_id} for SI {si_id}: {str(e)}")
            raise RuntimeError(f"Connection test failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Mono integration.
        
        Returns:
            Dict with health status
        """
        try:
            if self.mono_connector:
                return await self.mono_connector.health_check()
            else:
                return {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "connector": "not_initialized",
                    "config": {
                        "environment": self._config.environment
                    }
                }
                
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.mono_connector:
            await self.mono_connector.__aexit__(None, None, None)
            self.mono_connector = None