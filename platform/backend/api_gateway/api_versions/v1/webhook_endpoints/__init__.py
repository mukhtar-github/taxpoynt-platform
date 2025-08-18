"""
Webhook Endpoints - API v1
===========================

Webhook endpoints for processing real-time events from external services.

Available Webhooks:
- Mono Open Banking webhooks
- FIRS webhook callbacks (PRODUCTION READY)
- Payment processor webhooks (future)
"""

from .mono_webhook import create_mono_webhook_router
from .firs_webhook import create_firs_webhook_router

__all__ = [
    "create_mono_webhook_router",
    "create_firs_webhook_router"
]