"""
Payment Processor Webhook Endpoints
===================================

Minimal webhook receiver for payment processors (e.g., Paystack).
Verifies HMAC signature and routes events through the MessageRouter.
"""
from __future__ import annotations

import hmac
import hashlib
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse

from core_platform.messaging.message_router import MessageRouter, ServiceRole


class PaymentWebhookEndpoints:
    def __init__(self, message_router: MessageRouter):
        self.message_router = message_router
        self.router = APIRouter(prefix="/payments", tags=["Payment Webhooks"])
        self.paystack_secret = os.getenv("PAYSTACK_WEBHOOK_SECRET", "test_paystack_secret")
        self._setup_routes()

    def _setup_routes(self):
        self.router.add_api_route(
            "/callback",
            self.handle_payment_webhook,
            methods=["POST"],
            summary="Handle payment processor webhooks",
            response_model=None,
            status_code=200,
        )
        self.router.add_api_route(
            "/test",
            self.test_endpoint,
            methods=["GET"],
            summary="Test payment webhook",
        )

    async def handle_payment_webhook(
        self,
        request: Request,
        paystack_signature: Optional[str] = Header(None, alias="x-paystack-signature"),
    ) -> JSONResponse:
        try:
            raw = await request.body()
            body = raw.decode("utf-8")
            if not self._verify_paystack_signature(body, paystack_signature):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")

            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

            event = data.get("event") or data.get("event_type") or "payment.event"
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="process_payment_webhook",
                payload={
                    "event": event,
                    "data": data,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            return JSONResponse(
                status_code=200,
                content={"success": True, "action": "payment_webhook_processed", "data": result},
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def test_endpoint(self):
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", "endpoint": "/api/v1/webhooks/payments/callback"},
        )

    def _verify_paystack_signature(self, payload: str, signature: Optional[str]) -> bool:
        if not signature or not self.paystack_secret:
            return False
        expected = hmac.new(self.paystack_secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha512).hexdigest()
        return hmac.compare_digest(signature, expected)


def create_payment_webhook_router(message_router: MessageRouter) -> APIRouter:
    endpoints = PaymentWebhookEndpoints(message_router)
    return endpoints.router

