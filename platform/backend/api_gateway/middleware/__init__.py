"""
API Gateway Middleware Package
=============================
Comprehensive middleware stack for TaxPoynt API Gateway with role-based access control.
"""

# Export actual middleware classes implemented in this package
from .role_authenticator import RoleAuthenticator, create_role_authenticator
from .request_validator import RequestValidator, ValidationRule
from .rate_limiter import RoleBasedRateLimiter, RateLimitAlgorithm, RateLimitRule
from .request_transformer import RequestTransformer, TransformationRule, TransformationType
from .response_formatter import ResponseFormatter, ResponseFormatConfig

__all__ = [
    # Middleware classes
    "RoleAuthenticator",
    "RequestValidator",
    "RoleBasedRateLimiter",
    "RequestTransformer",
    "ResponseFormatter",

    # Factories / Config / Enums / Rules
    "create_role_authenticator",
    "ValidationRule",
    "RateLimitAlgorithm",
    "RateLimitRule",
    "TransformationRule",
    "TransformationType",
    "ResponseFormatConfig",
]
