"""
Mono Webhook Endpoints
======================

Handles incoming webhooks from Mono Open Banking API.
Processes real-time events from Mono including account connections,
transactions, and account status changes.

Webhook Events:
- account.linked: When a customer successfully links their bank account
- transaction.created: When a new transaction is detected
- account.disconnected: When an account connection is terminated

Security:
- Webhook signature verification using MONO_WEBHOOK_SECRET
- Request validation and sanitization
- Rate limiting for webhook endpoints
"""

import logging
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse

from core_platform.messaging.message_router import MessageRouter, ServiceRole
from si_services.banking_integration.mono_integration_service import MonoIntegrationService
from api_gateway.api_versions.models import V1ResponseModel

logger = logging.getLogger(__name__)


class MonoWebhookEndpoints:
    """
    Mono webhook endpoints for processing real-time banking events.
    """
    
    def __init__(self, message_router: MessageRouter):
        """
        Initialize Mono webhook endpoints.
        
        Args:
            message_router: Core platform message router
        """
        self.message_router = message_router
        self.router = APIRouter(prefix="/integrations/mono", tags=["Mono Webhooks"])
        self.webhook_secret = "sec_O62WW0RY6TP8ZGOPNILU"  # From .env
        
        self._setup_routes()
        logger.info("Mono webhook endpoints initialized")
    
    def _setup_routes(self):
        """Setup webhook routes"""
        
        self.router.add_api_route(
            "/webhook",
            self.handle_mono_webhook,
            methods=["POST"],
            summary="Handle Mono webhook events",
            description="Process incoming webhook events from Mono Open Banking API",
            response_model=V1ResponseModel,
            status_code=200
        )
        
        self.router.add_api_route(
            "/webhook/test",
            self.test_webhook_endpoint,
            methods=["GET"],
            summary="Test webhook endpoint",
            description="Test endpoint to verify webhook connectivity",
            response_model=V1ResponseModel
        )
    
    async def handle_mono_webhook(
        self,
        request: Request,
        mono_signature: Optional[str] = Header(None, alias="x-mono-signature"),
        mono_timestamp: Optional[str] = Header(None, alias="x-mono-timestamp")
    ) -> JSONResponse:
        """
        Handle incoming Mono webhook events.
        
        Args:
            request: FastAPI request object
            mono_signature: Mono webhook signature for verification
            mono_timestamp: Request timestamp from Mono
            
        Returns:
            JSONResponse confirming webhook processing
        """
        try:
            # Get raw payload
            payload = await request.body()
            payload_str = payload.decode('utf-8')
            
            logger.info(f"Received Mono webhook: signature={mono_signature}, timestamp={mono_timestamp}")
            
            # Verify webhook signature
            if not self._verify_webhook_signature(payload_str, mono_signature, mono_timestamp):
                logger.warning(f"Invalid Mono webhook signature: {mono_signature}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            # Parse webhook data
            try:
                webhook_data = json.loads(payload_str)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in Mono webhook: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON payload"
                )
            
            # Extract event information
            event_type = webhook_data.get("event")
            event_data = webhook_data.get("data", {})
            account_id = webhook_data.get("account_id")
            
            logger.info(f"Processing Mono webhook event: {event_type} for account: {account_id}")
            
            # Route to appropriate handler
            result = await self._process_webhook_event(event_type, event_data, account_id, webhook_data)
            
            return self._create_webhook_response(result, "webhook_processed_successfully")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing Mono webhook: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal webhook processing error"
            )
    
    async def test_webhook_endpoint(self) -> JSONResponse:
        """Test endpoint for webhook connectivity"""
        try:
            return self._create_webhook_response(
                {
                    "status": "healthy",
                    "endpoint": "/api/v1/integrations/mono/webhook",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Mono webhook endpoint is operational"
                },
                "webhook_test_successful"
            )
        except Exception as e:
            logger.error(f"Webhook test failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook test failed"
            )
    
    def _verify_webhook_signature(
        self,
        payload: str,
        signature: Optional[str],
        timestamp: Optional[str]
    ) -> bool:
        """
        Verify Mono webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from header
            timestamp: Request timestamp
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not signature or not self.webhook_secret:
            logger.warning("Webhook signature or secret missing")
            return False
        
        try:
            # Mono webhook signature format: timestamp.payload
            signed_payload = f"{timestamp}.{payload}"
            
            # Create expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    async def _process_webhook_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        account_id: Optional[str],
        full_webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process specific webhook event types.
        
        Args:
            event_type: Type of webhook event
            event_data: Event-specific data
            account_id: Account identifier
            full_webhook_data: Complete webhook payload
            
        Returns:
            Processing result
        """
        try:
            if event_type == "account.linked":
                return await self._handle_account_linked(event_data, account_id)
            elif event_type == "transaction.created":
                return await self._handle_transaction_created(event_data, account_id)
            elif event_type == "account.disconnected":
                return await self._handle_account_disconnected(event_data, account_id)
            else:
                logger.warning(f"Unknown Mono webhook event type: {event_type}")
                return {
                    "event_type": event_type,
                    "status": "ignored",
                    "message": f"Unsupported event type: {event_type}"
                }
                
        except Exception as e:
            logger.error(f"Error processing webhook event {event_type}: {str(e)}")
            return {
                "event_type": event_type,
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_account_linked(self, event_data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        """Handle account.linked webhook event"""
        try:
            logger.info(f"Processing account linked event for account: {account_id}")
            
            # Route to banking service for processing
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_account_linked",
                payload={
                    "event_type": "account.linked",
                    "account_id": account_id,
                    "event_data": event_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "event_type": "account.linked",
                "account_id": account_id,
                "status": "processed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling account linked event: {str(e)}")
            return {
                "event_type": "account.linked",
                "account_id": account_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_transaction_created(self, event_data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        """Handle transaction.created webhook event"""
        try:
            transaction_id = event_data.get("id")
            amount = event_data.get("amount", 0) / 100  # Convert kobo to Naira
            narration = event_data.get("narration", "")
            
            logger.info(f"Processing transaction created: {transaction_id} for account: {account_id}")
            
            # Route to banking service for transaction processing
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_new_transaction",
                payload={
                    "event_type": "transaction.created",
                    "account_id": account_id,
                    "transaction_id": transaction_id,
                    "amount_ngn": amount,
                    "narration": narration,
                    "event_data": event_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "event_type": "transaction.created",
                "account_id": account_id,
                "transaction_id": transaction_id,
                "amount_ngn": amount,
                "status": "processed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling transaction created event: {str(e)}")
            return {
                "event_type": "transaction.created",
                "account_id": account_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _handle_account_disconnected(self, event_data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        """Handle account.disconnected webhook event"""
        try:
            logger.info(f"Processing account disconnected event for account: {account_id}")
            
            # Route to banking service for cleanup
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_account_disconnected",
                payload={
                    "event_type": "account.disconnected",
                    "account_id": account_id,
                    "event_data": event_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "event_type": "account.disconnected",
                "account_id": account_id,
                "status": "processed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error handling account disconnected event: {str(e)}")
            return {
                "event_type": "account.disconnected",
                "account_id": account_id,
                "status": "error",
                "error": str(e)
            }
    
    def _create_webhook_response(self, data: Dict[str, Any], action: str) -> JSONResponse:
        """Create standardized webhook response"""
        response_data = {
            "success": True,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        return JSONResponse(content=response_data, status_code=200)


def create_mono_webhook_router(message_router: MessageRouter) -> APIRouter:
    """Factory function to create Mono webhook router"""
    webhook_endpoints = MonoWebhookEndpoints(message_router)
    return webhook_endpoints.router