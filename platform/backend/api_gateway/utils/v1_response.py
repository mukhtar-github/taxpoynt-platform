"""
V1 Response Helper
==================

Provides a single helper to build V1ResponseModel instances to keep
responses consistent and eliminate hardcoded timestamps.
"""
from __future__ import annotations

from typing import Any
from ..api_versions.v1.si_endpoints.version_models import V1ResponseModel


def build_v1_response(data: Any, action: str) -> V1ResponseModel:
    """Create a standardized V1ResponseModel."""
    return V1ResponseModel(action=action, data=data)


__all__ = ["build_v1_response"]

