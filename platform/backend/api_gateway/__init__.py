"""
TaxPoynt API Gateway
===================
Central API gateway system for the TaxPoynt platform providing role-based
routing, authentication, and access control for all platform services.

**Architecture:**
- Role-based routing for SI, APP, and Hybrid users
- Centralized authentication and authorization
- API versioning and endpoint management
- Request/response middleware and monitoring
"""

from .role_routing import (
    TaxPoyntAPIGateway,
    create_si_router,
    create_app_router,
    create_hybrid_router,
    create_auth_router
)

__all__ = [
    "TaxPoyntAPIGateway",
    "create_si_router", 
    "create_app_router",
    "create_hybrid_router",
    "create_auth_router"
]