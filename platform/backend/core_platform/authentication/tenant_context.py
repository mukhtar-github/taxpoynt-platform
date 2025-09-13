"""
Tenant Context
==============

Lightweight ContextVar-based tenant context utilities. This scaffolding allows
request-scoped tenant IDs to be set and retrieved without imposing a specific
web framework or database pattern.

Integrations can set the tenant at request entry (e.g., from an HTTP routing
context) and repositories can read it to enforce tenant filtering.
"""
from __future__ import annotations

from contextvars import ContextVar
from contextlib import contextmanager
from typing import Optional, Iterator

_current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)


def set_current_tenant(tenant_id: Optional[str]) -> None:
    """Set current tenant id in ContextVar (None clears)."""
    _current_tenant_id.set(tenant_id)


def get_current_tenant() -> Optional[str]:
    """Get current tenant id from ContextVar."""
    return _current_tenant_id.get()


def clear_current_tenant() -> None:
    """Clear tenant id from ContextVar."""
    _current_tenant_id.set(None)


@contextmanager
def tenant_context(tenant_id: Optional[str]) -> Iterator[None]:
    """Context manager to temporarily set tenant id."""
    token = _current_tenant_id.set(tenant_id)
    try:
        yield
    finally:
        _current_tenant_id.reset(token)


def apply_tenant_from_obj(obj: object) -> Optional[str]:
    """Best-effort: extract 'tenant_id' from an arbitrary object or dict and set it.

    Returns the tenant_id that was applied (or None).
    """
    tenant_id: Optional[str] = None
    try:
        if isinstance(obj, dict):
            tenant_id = obj.get("tenant_id")  # type: ignore[assignment]
        else:
            tenant_id = getattr(obj, "tenant_id", None)
    except Exception:
        tenant_id = None
    set_current_tenant(tenant_id)
    return tenant_id


__all__ = [
    "set_current_tenant",
    "get_current_tenant",
    "clear_current_tenant",
    "tenant_context",
    "apply_tenant_from_obj",
]

