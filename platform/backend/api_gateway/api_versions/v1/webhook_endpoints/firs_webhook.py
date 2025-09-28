"""
FIRS Webhook Endpoints
======================

Handles incoming webhooks from FIRS (Federal Inland Revenue Service).
Processes real-time callbacks for invoice submissions, validations, and status updates.

Based on existing infrastructure:
- platform/backend/app_services/webhook_services/webhook_receiver.py
- legacy/backend/app/routes/firs_certification_webhooks.py
- platform/backend/core_platform/data_management/models/firs_submission.py

FIRS Webhook Events:
- invoice.submitted: Invoice successfully submitted to FIRS
- invoice.accepted: Invoice approved by FIRS  
- invoice.rejected: Invoice rejected by FIRS
- irn.generated: IRN successfully generated
- irn.cancelled: IRN cancelled by FIRS
- validation.completed: Document validation results
- transmission.status: Transmission status updates
"""

import logging
import hmac
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Header, status, Depends
from fastapi.responses import JSONResponse

from core_platform.messaging.message_router import MessageRouter, ServiceRole
from app_services.webhook_services.webhook_receiver import WebhookReceiver
from app_services.status_management.callback_manager import CallbackManager
from api_gateway.api_versions.models import V1ResponseModel
from prometheus_client import Counter, Histogram

from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.db_async import get_async_session
from core_platform.idempotency.store import IdempotencyStore

logger = logging.getLogger(__name__)


@dataclass
class _WebhookIdempotencyContext:
    key: str
    requester_id: str
    stored_response: Optional[Dict[str, Any]] = None
    status_code: int = 200
    should_finalize: bool = False


class FIRSWebhookEndpoints:
    """
    FIRS webhook endpoints for processing real-time FIRS callbacks.
    
    Integrates with existing webhook infrastructure and FIRS submission models.
    """
    
    def __init__(self, message_router: MessageRouter):
        """
        Initialize FIRS webhook endpoints.
        
        Args:
            message_router: Core platform message router
        """
        self.message_router = message_router
        self.router = APIRouter(prefix="/webhooks/firs", tags=["FIRS Webhooks"])
        secret = os.getenv("FIRS_WEBHOOK_SECRET")
        if not secret:
            logger.warning("FIRS_WEBHOOK_SECRET not set; using development placeholder secret")
            secret = "development-placeholder-secret"
        self.webhook_secret = secret
        
        # Initialize webhook receiver and callback manager
        self.webhook_receiver = WebhookReceiver(self.webhook_secret)
        self.callback_manager = CallbackManager()
        
        self._setup_routes()
        logger.info("FIRS webhook endpoints initialized")

        # Metrics
        self.metric_events_total = Counter(
            "firs_webhook_events_total",
            "Total FIRS webhook events processed",
            ["event_type", "outcome"],
            registry=None,
        )
        self.metric_process_seconds = Histogram(
            "firs_webhook_process_seconds",
            "Time spent processing FIRS webhook events",
            registry=None,
        )
    
    def _setup_routes(self):
        """Setup FIRS webhook routes"""
        
        # Unified FIRS webhook endpoint (recommended)
        self.router.add_api_route(
            "/callback",
            self.handle_firs_webhook,
            methods=["POST"],
            summary="Handle FIRS webhook callbacks",
            description="Process all FIRS webhook events (invoice status, IRN updates, validations)",
            response_model=V1ResponseModel,
            status_code=200
        )
        
        # Legacy specific endpoints for backward compatibility
        self.router.add_api_route(
            "/invoice-status",
            self.handle_invoice_status_webhook,
            methods=["POST"],
            summary="Handle invoice status webhooks",
            description="Process FIRS invoice status updates",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/transmission-status",
            self.handle_transmission_status_webhook,
            methods=["POST"],
            summary="Handle transmission status webhooks",
            description="Process FIRS transmission status updates",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/validation-result",
            self.handle_validation_result_webhook,
            methods=["POST"],
            summary="Handle validation result webhooks",
            description="Process FIRS validation results",
            response_model=V1ResponseModel
        )
        
        # Test endpoint
        self.router.add_api_route(
            "/test",
            self.test_firs_webhook_endpoint,
            methods=["GET"],
            summary="Test FIRS webhook endpoint",
            description="Test endpoint to verify FIRS webhook connectivity",
            response_model=V1ResponseModel
        )
    
    async def _start_webhook_idempotency(
        self,
        *,
        request: Request,
        payload: Dict[str, Any],
        db: AsyncSession,
    ) -> Optional[_WebhookIdempotencyContext]:
        idem_key = request.headers.get("x-request-id") or payload.get("event_id") or payload.get("eventId")
        if not idem_key:
            return None

        key = str(idem_key)
        request_hash = IdempotencyStore.compute_request_hash(payload or {})

        exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
            db,
            requester_id="firs_webhook",
            key=key,
            method=request.method,
            endpoint=str(request.url.path),
            request_hash=request_hash,
        )

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="x-request-id already processed with different webhook payload",
            )

        return _WebhookIdempotencyContext(
            key=key,
            requester_id="firs_webhook",
            stored_response=stored,
            status_code=stored_code or 200,
            should_finalize=stored is None,
        )

    async def _finalize_webhook_idempotency(
        self,
        ctx: Optional[_WebhookIdempotencyContext],
        db: AsyncSession,
        response_payload: Dict[str, Any],
        status_code: int = 200,
    ) -> None:
        if not ctx or not ctx.key or not ctx.should_finalize:
            return

        await IdempotencyStore.finalize_success(
            db,
            requester_id=ctx.requester_id,
            key=ctx.key,
            response=response_payload,
            status_code=status_code,
        )

    def _build_webhook_response_data(self, data: Dict[str, Any], action: str) -> Dict[str, Any]:
        return {
            "success": True,
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

    async def handle_firs_webhook(
        self,
        request: Request,
        x_firs_signature: Optional[str] = Header(None, alias="x-firs-signature"),
        x_firs_timestamp: Optional[str] = Header(None, alias="x-firs-timestamp"),
        x_firs_event: Optional[str] = Header(None, alias="x-firs-event"),
        db: AsyncSession = Depends(get_async_session),
    ) -> JSONResponse:
        """
        Handle unified FIRS webhook callbacks.
        
        Args:
            request: FastAPI request object
            x_firs_signature: FIRS webhook signature for verification
            x_firs_timestamp: Request timestamp from FIRS
            x_firs_event: Event type from FIRS
            
        Returns:
            JSONResponse confirming webhook processing
        """
        try:
            start_time = datetime.utcnow().timestamp()
            # Get raw payload
            payload = await request.body()
            payload_str = payload.decode('utf-8')
            
            logger.info(f"Received FIRS webhook: event={x_firs_event}, signature={x_firs_signature}")
            
            # Verify webhook signature
            if not self._verify_firs_signature(payload_str, x_firs_signature, x_firs_timestamp):
                logger.warning(f"Invalid FIRS webhook signature: {x_firs_signature}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
            
            # Parse webhook data
            try:
                webhook_data = json.loads(payload_str)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in FIRS webhook: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON payload"
                )
            
            # Extract event information
            event_type = x_firs_event or webhook_data.get("event_type")
            submission_id = webhook_data.get("submission_id")
            irn = webhook_data.get("irn")
            status_data = webhook_data.get("status", {})
            
            logger.info(f"Processing FIRS webhook: {event_type} for submission: {submission_id}")
            
            idem_ctx = await self._start_webhook_idempotency(
                request=request,
                payload=webhook_data,
                db=db,
            )

            if idem_ctx and idem_ctx.stored_response is not None:
                return JSONResponse(
                    content=idem_ctx.stored_response,
                    status_code=idem_ctx.status_code,
                    headers={"X-Idempotent-Replay": "true"},
                )

            # Process webhook using existing webhook receiver
            result = await self._process_firs_webhook_event(
                event_type, webhook_data, submission_id, irn, status_data
            )
            self.metric_events_total.labels(event_type or "unknown", "success").inc()
            self.metric_process_seconds.observe(datetime.utcnow().timestamp() - start_time)

            response_payload = self._build_webhook_response_data(result, "firs_webhook_processed")

            await self._finalize_webhook_idempotency(idem_ctx, db, response_payload)

            return JSONResponse(content=response_payload, status_code=200)
            
        except HTTPException:
            if 'event_type' in locals():
                self.metric_events_total.labels(event_type or "unknown", "error").inc()
            raise
        except Exception as e:
            logger.error(f"Error processing FIRS webhook: {str(e)}", exc_info=True)
            if 'event_type' in locals():
                self.metric_events_total.labels(event_type or "unknown", "error").inc()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal webhook processing error"
            )
    
    async def handle_invoice_status_webhook(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ) -> JSONResponse:
        """Handle legacy invoice status webhook format"""
        return await self._handle_legacy_webhook(request, "invoice.status", db)

    async def handle_transmission_status_webhook(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ) -> JSONResponse:
        """Handle legacy transmission status webhook format"""
        return await self._handle_legacy_webhook(request, "transmission.status", db)

    async def handle_validation_result_webhook(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ) -> JSONResponse:
        """Handle legacy validation result webhook format"""
        return await self._handle_legacy_webhook(request, "validation.result", db)
    
    async def test_firs_webhook_endpoint(self) -> JSONResponse:
        """Test endpoint for FIRS webhook connectivity"""
        try:
            return self._create_webhook_response(
                {
                    "status": "healthy",
                    "endpoint": "/api/v1/webhooks/firs/callback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "FIRS webhook endpoint is operational",
                    "supported_events": [
                        "invoice.submitted",
                        "invoice.accepted", 
                        "invoice.rejected",
                        "irn.generated",
                        "irn.cancelled",
                        "validation.completed",
                        "transmission.status"
                    ]
                },
                "firs_webhook_test_successful"
            )
        except Exception as e:
            logger.error(f"FIRS webhook test failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="FIRS webhook test failed"
            )
    
    async def _handle_legacy_webhook(
        self,
        request: Request,
        event_type: str,
        db: AsyncSession,
    ) -> JSONResponse:
        """Handle legacy webhook formats for backward compatibility"""
        try:
            payload = await request.body()
            payload_str = payload.decode('utf-8')
            webhook_data = json.loads(payload_str)

            idem_ctx = await self._start_webhook_idempotency(
                request=request,
                payload=webhook_data,
                db=db,
            )

            if idem_ctx and idem_ctx.stored_response is not None:
                return JSONResponse(
                    content=idem_ctx.stored_response,
                    status_code=idem_ctx.status_code,
                    headers={"X-Idempotent-Replay": "true"},
                )

            # Process using unified handler
            result = await self._process_firs_webhook_event(
                event_type,
                webhook_data,
                webhook_data.get("submission_id"),
                webhook_data.get("irn"),
                webhook_data.get("status", {}),
            )

            response_payload = self._build_webhook_response_data(result, f"firs_{event_type}_processed")

            await self._finalize_webhook_idempotency(idem_ctx, db, response_payload)

            return JSONResponse(content=response_payload, status_code=200)
            
        except Exception as e:
            logger.error(f"Error processing legacy FIRS webhook {event_type}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process {event_type} webhook"
            )
    
    def _verify_firs_signature(
        self,
        payload: str,
        signature: Optional[str],
        timestamp: Optional[str]
    ) -> bool:
        """
        Verify FIRS webhook signature using HMAC SHA256.
        
        Based on existing verification from webhook_verification_service.py
        """
        if not signature or not self.webhook_secret:
            logger.warning("FIRS webhook signature or secret missing")
            return False
        
        try:
            # FIRS webhook signature format: timestamp.payload
            signed_payload = f"{timestamp}.{payload}"
            
            # Create expected signature using HMAC SHA256
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying FIRS webhook signature: {str(e)}")
            return False
    
    async def _process_firs_webhook_event(
        self,
        event_type: str,
        webhook_data: Dict[str, Any],
        submission_id: Optional[str],
        irn: Optional[str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process FIRS webhook events using message router and existing services.
        
        Routes to APP services for FIRS-related operations.
        """
        try:
            # Route to APP service for FIRS webhook processing
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="process_firs_webhook",
                payload={
                    "event_type": event_type,
                    "submission_id": submission_id,
                    "irn": irn,
                    "status_data": status_data,
                    "webhook_data": webhook_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Update submission status based on event type
            await self._update_submission_status(event_type, submission_id, irn, status_data)
            
            # Handle specific event types
            if event_type in ["invoice.accepted", "irn.generated"]:
                await self._handle_successful_submission(submission_id, irn, webhook_data)
            elif event_type in ["invoice.rejected", "validation.failed"]:
                await self._handle_failed_submission(submission_id, status_data, webhook_data)
            
            return {
                "event_type": event_type,
                "submission_id": submission_id,
                "irn": irn,
                "status": "processed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error processing FIRS webhook event {event_type}: {str(e)}")
            return {
                "event_type": event_type,
                "submission_id": submission_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _update_submission_status(
        self,
        event_type: str,
        submission_id: Optional[str],
        irn: Optional[str],
        status_data: Dict[str, Any]
    ):
        """Update FIRS submission status in database"""
        try:
            if not submission_id:
                return
            
            # Map event types to submission statuses
            status_mapping = {
                "invoice.submitted": "SUBMITTED",
                "invoice.accepted": "ACCEPTED",
                "invoice.rejected": "REJECTED",
                "irn.generated": "ACCEPTED",
                "irn.cancelled": "CANCELLED",
                "validation.completed": "SUBMITTED",
                "validation.failed": "REJECTED",
                "transmission.status": "PROCESSING"
            }
            
            new_status = status_mapping.get(event_type, "PROCESSING")
            
            # Route to APP service for database update
            await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_firs_submission_status",
                payload={
                    "submission_id": submission_id,
                    "new_status": new_status,
                    "irn": irn,
                    "firs_response": status_data,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Updated submission {submission_id} status to {new_status}")
            
        except Exception as e:
            logger.error(f"Error updating submission status: {str(e)}")
    
    async def _handle_successful_submission(
        self,
        submission_id: Optional[str],
        irn: Optional[str],
        webhook_data: Dict[str, Any]
    ):
        """Handle successful FIRS submission"""
        try:
            # Notify customer of successful submission
            await self.callback_manager.send_callback(
                callback_type="completion",
                data={
                    "submission_id": submission_id,
                    "irn": irn,
                    "status": "SUCCESS",
                    "message": "Invoice successfully processed by FIRS",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Notified customer of successful submission: {submission_id}")
            
        except Exception as e:
            logger.error(f"Error handling successful submission: {str(e)}")
    
    async def _handle_failed_submission(
        self,
        submission_id: Optional[str],
        status_data: Dict[str, Any],
        webhook_data: Dict[str, Any]
    ):
        """Handle failed FIRS submission"""
        try:
            error_message = status_data.get("error_message", "Unknown error")
            error_code = status_data.get("error_code", "UNKNOWN")
            
            # Notify customer of failed submission
            await self.callback_manager.send_callback(
                callback_type="error_notification",
                data={
                    "submission_id": submission_id,
                    "status": "FAILED",
                    "error_code": error_code,
                    "error_message": error_message,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Notified customer of failed submission: {submission_id}")
            
        except Exception as e:
            logger.error(f"Error handling failed submission: {str(e)}")
    
    def _create_webhook_response(self, data: Dict[str, Any], action: str) -> JSONResponse:
        """Create standardized webhook response"""
        response_data = self._build_webhook_response_data(data, action)
        return JSONResponse(content=response_data, status_code=200)


def create_firs_webhook_router(message_router: MessageRouter) -> APIRouter:
    """Factory function to create FIRS webhook router"""
    webhook_endpoints = FIRSWebhookEndpoints(message_router)
    return webhook_endpoints.router
