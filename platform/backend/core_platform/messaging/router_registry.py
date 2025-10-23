
"""
Message Router Registry
=======================

Provides a shared registry for the active message router so utilities such as
the async health checker can obtain the instance without creating duplicates.
This avoids repeatedly instantiating Redis-backed routers during health checks.
"""

from __future__ import annotations

from typing import Optional

from .message_router import MessageRouter

# Module-level cache of the active message router. The application startup
# registers the instance once and health checks can reuse it.
_message_router: Optional[MessageRouter] = None


def set_message_router(router: MessageRouter) -> None:
    """Register the active message router for later reuse."""
    global _message_router
    _message_router = router


def get_message_router() -> Optional[MessageRouter]:
    """Retrieve the registered message router, if any."""
    return _message_router
