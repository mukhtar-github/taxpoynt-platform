"""
API Gateway Role Routing Models
==============================
HTTP-specific data models for role-based API routing that extend the existing
NEW architecture role management components.
"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from fastapi import Request, Response

# Import from NEW architecture core components with fixed paths
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from core_platform.authentication.role_manager import PlatformRole, RoleScope
    from core_platform.messaging.message_router import ServiceRole
except ImportError:
    # Fallback enums for development
    from enum import Enum
    
    class PlatformRole(Enum):
        SYSTEM_INTEGRATOR = "system_integrator"
        ACCESS_POINT_PROVIDER = "access_point_provider"
        HYBRID = "hybrid"
        PLATFORM_ADMIN = "platform_admin"
        TENANT_ADMIN = "tenant_admin"
        USER = "user"
    
    class RoleScope(Enum):
        GLOBAL = "global"
        TENANT = "tenant"
        SERVICE = "service"
        ENVIRONMENT = "environment"
    
    class ServiceRole(Enum):
        SYSTEM_INTEGRATOR = "si"
        ACCESS_POINT_PROVIDER = "app"
        HYBRID = "hybrid"
        HYBRID_COORDINATOR = "hybrid_coordinator"
        CORE = "core"


class HTTPMethod(Enum):
    """HTTP methods for API routing."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class RouteType(Enum):
    """Types of API routes."""
    SI_ONLY = "si_only"                    # System Integrator only
    APP_ONLY = "app_only"                  # Access Point Provider only
    HYBRID = "hybrid"                      # Cross-role functionality
    PUBLIC = "public"                      # Public endpoints
    ADMIN = "admin"                        # Administrative endpoints
    HEALTH = "health"                      # Health check endpoints


class PermissionLevel(Enum):
    """Permission levels for API access."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    EXECUTE = "execute"
    DELETE = "delete"


class RoutingSecurityLevel(Enum):
    """Security levels for API routing."""
    STRICT = "strict"
    STANDARD = "standard"
    RELAXED = "relaxed"


@dataclass
class APIGatewayConfig:
    """Configuration for API Gateway."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    trusted_hosts: Optional[List[str]] = None
    security: RoutingSecurityLevel = RoutingSecurityLevel.STANDARD
    
    # Authentication settings
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 1440  # 24 hours
    
    # Rate limiting
    enable_rate_limiting: bool = True
    default_rate_limit: int = 100  # requests per minute
    
    # Logging and monitoring
    enable_request_logging: bool = True
    enable_metrics: bool = True
    log_level: str = "INFO"


@dataclass
class HTTPRoutingContext:
    """Context for HTTP request routing."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    platform_role: Optional[PlatformRole] = None
    service_role: Optional[ServiceRole] = None
    role_scope: Optional[RoleScope] = None
    permissions: List[str] = field(default_factory=list)
    session_id: Optional[str] = None
    api_key: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    request_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_authenticated: bool = False  # Add missing authentication flag
    _primary_role: Optional[PlatformRole] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self._primary_role is None and self.platform_role is not None:
            self._primary_role = self.platform_role
        elif self._primary_role is not None and self.platform_role is None:
            self.platform_role = self._primary_role

    def has_role(self, role: PlatformRole) -> bool:
        """Check if context has the specified platform role"""
        return self.platform_role == role

    @property
    def primary_role(self) -> Optional[PlatformRole]:
        """Alias for legacy callers expecting primary_role attribute."""
        return self._primary_role or self.platform_role

    @primary_role.setter
    def primary_role(self, value: Optional[PlatformRole]) -> None:
        self._primary_role = value
        if value is not None:
            self.platform_role = value


@dataclass
class RequestAnalysis:
    """Analysis result of HTTP request for role detection."""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_path: str = ""
    http_method: HTTPMethod = HTTPMethod.GET
    detected_roles: List[PlatformRole] = field(default_factory=list)
    confidence_score: float = 0.0
    route_type: Optional[RouteType] = None
    required_permissions: List[str] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Request characteristics
    has_authentication: bool = False
    authentication_method: Optional[str] = None
    request_size_bytes: int = 0
    content_type: Optional[str] = None
    
    # Role indicators
    si_indicators: List[str] = field(default_factory=list)
    app_indicators: List[str] = field(default_factory=list)
    hybrid_indicators: List[str] = field(default_factory=list)
    
    # Security analysis
    security_flags: List[str] = field(default_factory=list)
    risk_score: float = 0.0


@dataclass
class RoutePermission:
    """Permission configuration for API routes."""
    permission_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    route_pattern: str = ""
    required_roles: List[PlatformRole] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    permission_level: PermissionLevel = PermissionLevel.READ
    scope: RoleScope = RoleScope.TENANT
    allowed_methods: List[HTTPMethod] = field(default_factory=list)
    
    # Access control
    require_authentication: bool = True
    require_api_key: bool = False
    rate_limit_per_minute: Optional[int] = None
    
    # Conditions
    ip_whitelist: List[str] = field(default_factory=list)
    time_restrictions: Optional[Dict[str, Any]] = None
    organization_restrictions: List[str] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class APIEndpointRule:
    """Rule for API endpoint routing and access control."""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Route matching
    path_pattern: str = ""
    methods: List[HTTPMethod] = field(default_factory=list)
    route_type: RouteType = RouteType.PUBLIC
    
    # Role and permission requirements
    allowed_platform_roles: List[PlatformRole] = field(default_factory=list)
    allowed_service_roles: List[ServiceRole] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    permission_level: PermissionLevel = PermissionLevel.READ
    
    # Target service routing
    target_service_pattern: str = ""
    target_service_role: Optional[ServiceRole] = None
    forward_to_message_router: bool = True
    
    # Access control
    require_authentication: bool = True
    require_organization_context: bool = True
    require_tenant_context: bool = False
    
    # Rate limiting and throttling
    rate_limit_per_minute: Optional[int] = None
    burst_limit: Optional[int] = None
    
    # Request/Response transformation
    request_transformers: List[str] = field(default_factory=list)
    response_transformers: List[str] = field(default_factory=list)
    
    # Validation
    validate_request_schema: bool = True
    validate_response_schema: bool = False
    schema_definitions: Dict[str, Any] = field(default_factory=dict)
    
    # Monitoring and logging
    enable_detailed_logging: bool = False
    track_performance_metrics: bool = True
    enable_audit_trail: bool = True
    
    # Rule metadata
    priority: int = 0
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = field(default_factory=list)


@dataclass
class RoleBasedRoute:
    """Configuration for role-based FastAPI route."""
    route_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    path: str = ""
    methods: List[HTTPMethod] = field(default_factory=list)
    route_type: RouteType = RouteType.PUBLIC
    
    # Handler configuration
    handler_function: Optional[Callable] = None
    handler_module: Optional[str] = None
    handler_class: Optional[str] = None
    
    # Role requirements
    allowed_roles: List[PlatformRole] = field(default_factory=list)
    required_permissions: List[str] = field(default_factory=list)
    
    # FastAPI route configuration
    summary: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    response_model: Optional[Any] = None
    status_code: int = 200
    
    # Middleware configuration
    apply_role_middleware: bool = True
    apply_rate_limiting: bool = True
    apply_request_validation: bool = True
    
    # Dependencies
    dependencies: List[Callable] = field(default_factory=list)
    
    # Route metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    enabled: bool = True


@dataclass
class RoutingDecision:
    """Decision result for request routing."""
    request_context: HTTPRoutingContext
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_router: str = ""  # si, app, or hybrid
    target_service: Optional[str] = None
    allowed: bool = False
    
    # Decision reasoning
    applied_rules: List[str] = field(default_factory=list)
    permission_checks: Dict[str, bool] = field(default_factory=dict)
    role_validation_results: Dict[str, Any] = field(default_factory=dict)
    
    # Actions to take
    forward_to_message_router: bool = False
    apply_transformations: List[str] = field(default_factory=list)
    response_modifications: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    decision_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = 0.0
    cache_key: Optional[str] = None


@dataclass
class RouteMetrics:
    """Metrics for API route performance tracking."""
    route_id: str
    path_pattern: str
    method: HTTPMethod
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    # Response time metrics
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # Role-based metrics
    si_requests: int = 0
    app_requests: int = 0
    hybrid_requests: int = 0
    admin_requests: int = 0
    
    # Error metrics
    authentication_failures: int = 0
    authorization_failures: int = 0
    validation_failures: int = 0
    rate_limit_violations: int = 0
    
    # Time-based tracking
    last_request_timestamp: Optional[datetime] = None
    metrics_period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metrics_period_end: Optional[datetime] = None


# Type aliases for convenience
HTTPRequestHandler = Callable[[Request], Union[Response, Dict[str, Any]]]
RouteMiddleware = Callable[[Request, Callable], Response]
RequestTransformer = Callable[[Request, HTTPRoutingContext], Request]
ResponseTransformer = Callable[[Response, HTTPRoutingContext], Response]

# Export all public classes and enums
__all__ = [
    # Enums
    'PlatformRole',
    'RoleScope', 
    'ServiceRole',
    'HTTPMethod',
    'RouteType',
    'PermissionLevel',
    'RoutingSecurityLevel',
    
    # Data Classes
    'HTTPRoutingContext',
    'APIEndpointRule', 
    'RoleBasedRoute',
    'RequestAnalysis',
    'RoutePermission',
    'RouteMetrics',
    'APIGatewayConfig',
    
    # Type aliases
    'HTTPRequestHandler',
    'RouteMiddleware', 
    'RequestTransformer',
    'ResponseTransformer'
]
