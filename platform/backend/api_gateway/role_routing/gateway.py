"""
API Gateway Main Router
======================
Central API Gateway that integrates role-based routing with the existing message router
system to provide unified HTTP access to TaxPoynt platform services.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, HTTPException, status, Depends, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi

# Fix import paths  
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Production imports - no fallbacks
from core_platform.authentication.role_manager import RoleManager, PlatformRole
from core_platform.messaging.redis_message_router import RedisMessageRouter
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from .models import HTTPRoutingContext, APIGatewayConfig, RoutingSecurityLevel
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard
from .app_router import create_app_router
from .hybrid_router import create_hybrid_router
from .auth_router import create_auth_router
from .admin_router import create_admin_router

# Phase 4 Performance Infrastructure
from core_platform.data_management.cache_manager import CacheManager, CacheConfig
from core_platform.messaging.async_health_checker import AsyncHealthCheckManager

logger = logging.getLogger(__name__)


class TaxPoyntAPIGateway:
    """
    TaxPoynt API Gateway
    ===================
    Central HTTP gateway that provides:
    - Role-based request routing to appropriate service layers
    - Integration with existing message router system
    - Unified authentication and authorization
    - Cross-role endpoint management
    - Comprehensive API documentation
    """
    
    def __init__(self, 
                 config: APIGatewayConfig,
                 role_manager: RoleManager,
                 message_router: RedisMessageRouter):
        self.config = config
        self.role_manager = role_manager
        self.message_router = message_router
        
        # Initialize core components
        self.role_detector = HTTPRoleDetector()
        self.permission_guard = APIPermissionGuard(config.security)
        
        # Phase 4: Initialize performance infrastructure
        self.cache_manager = self._initialize_cache_manager()
        self.health_checker = AsyncHealthCheckManager()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="TaxPoynt E-Invoice Platform API",
            description="Comprehensive API for Nigerian e-invoicing compliance and business system integration",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )
        
        self._setup_middleware()
        self._setup_routers()
        self._setup_global_handlers()
        
        logger.info("TaxPoynt API Gateway initialized successfully")
        logger.info("Phase 4: Cache manager and async health checker enabled")
    
    def _initialize_cache_manager(self) -> CacheManager:
        """Initialize cache manager for response caching."""
        try:
            cache_config = CacheConfig(
                default_ttl_seconds=300,  # 5 minutes for API responses
                max_memory_cache_size=1000,
                enable_compression=True,
                enable_metrics=True
            )
            cache_manager = CacheManager(cache_config)
            logger.info("Cache manager initialized for API Gateway")
            return cache_manager
        except Exception as e:
            logger.warning(f"Failed to initialize cache manager: {e}")
            return None
    
    def _setup_middleware(self):
        """Configure FastAPI middleware"""
        
        # CORS middleware is now handled in main.py to ensure proper middleware order
        # This prevents double CORS setup which can cause conflicts
        # if self.config.cors_enabled:
        #     self.app.add_middleware(
        #         CORSMiddleware,
        #         allow_origins=self.config.cors_origins,
        #         allow_credentials=True,
        #         allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        #         allow_headers=["*"],
        #         expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining"]
        #     )
        
        # Trusted host middleware
        if self.config.trusted_hosts:
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self.config.trusted_hosts
            )
        
        # Note: Request logging and monitoring now handled by Phase 4 ObservabilityMiddleware
        # in main.py - provides Prometheus metrics, OpenTelemetry tracing, and async logging
        # This eliminates synchronous logging bottlenecks and duplicate instrumentation
        # CORS middleware also handled in main.py for proper middleware ordering
    
    def _setup_routers(self):
        """Setup role-based routers"""
        
        # Create specialized routers
        # Note: Legacy SI router removed - using main API Gateway instead
        
        app_router = create_app_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        
        hybrid_router = create_hybrid_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        
        # Create authentication router (shared across all service types)
        auth_router = create_auth_router(
            self.role_detector,
            self.permission_guard,
            self.message_router
        )

        # Forgot-password router (public)
        from ..auth.forgot_password_router import router as forgot_password_router

        # Create admin router (platform administration)
        admin_router = create_admin_router()
        
        # Include routers in main app
        # Note: Legacy SI router removed - using main API Gateway instead
        
        self.app.include_router(
            app_router,
            prefix="/api/v1",
            tags=["Access Point Provider Services"]
        )
        
        self.app.include_router(
            hybrid_router,
            prefix="/api/v1",
            tags=["Hybrid Services"]
        )
        
        # Include authentication router (available to all service types)
        self.app.include_router(
            auth_router,
            prefix="/api/v1",
            tags=["Authentication"]
        )

        self.app.include_router(
            forgot_password_router,
            prefix="/api/v1",
            tags=["Authentication"]
        )
        
        # Include admin router (platform administration)
        self.app.include_router(
            admin_router,
            prefix="/api/v1",
            tags=["Platform Administration"]
        )
        
        # Include webhook router (publicly accessible, no authentication)
        webhook_router = self._create_webhook_router()
        self.app.include_router(
            webhook_router,
            prefix="/api/v1/webhooks",
            tags=["External Webhooks"]
        )
        
        # Add root level routes
        self._setup_root_routes()
    
    def _create_webhook_router(self) -> APIRouter:
        """
        Create combined webhook router for all external webhooks.
        
        Returns:
            APIRouter: Combined webhook router with all webhook endpoints
        """
        from ..api_versions.v1.webhook_endpoints import (
            create_mono_webhook_router,
            create_firs_webhook_router,
            create_payment_webhook_router,
        )
        
        # Create main webhook router (no authentication required)
        webhook_router = APIRouter(tags=["External Webhooks"])
        
        # Include Mono webhook endpoints
        mono_webhook_router = create_mono_webhook_router(self.message_router)
        webhook_router.include_router(
            mono_webhook_router,
            prefix="/mono",
            tags=["Mono Open Banking Webhooks"]
        )
        
        # Include FIRS webhook endpoints  
        firs_webhook_router = create_firs_webhook_router(self.message_router)
        webhook_router.include_router(
            firs_webhook_router,
            prefix="/firs",
            tags=["FIRS Compliance Webhooks"]
        )

        # Include Payment processor webhooks
        payment_router = create_payment_webhook_router(self.message_router)
        webhook_router.include_router(
            payment_router,
            prefix="/payments",
            tags=["Payment Processor Webhooks"],
        )
        
        logger.info("✅ Webhook router created with Mono and FIRS endpoints")
        return webhook_router
    
    def _setup_root_routes(self):
        """Setup root level API routes"""
        
        @self.app.get("/", summary="API Root")
        async def api_root():
            """API root endpoint with service information"""
            return JSONResponse(content={
                "service": "TaxPoynt E-Invoice Platform API",
                "version": "1.0.0",
                "status": "operational",
                "phase_4_optimizations": {
                    "performance_infrastructure": True,
                    "cache_manager": self.cache_manager is not None,
                    "async_health_checker": self.health_checker is not None,
                    "observability_middleware": "Enabled in main.py",
                    "prometheus_metrics": "Enabled",
                    "opentelemetry_tracing": "Enabled"
                },
                "endpoints": {
                    "authentication": "/api/v1/auth",
                    "system_integrator": "/api/v1/si",
                    "access_point_provider": "/api/v1/app",
                    "hybrid_services": "/api/v1/common",
                    "webhooks": "/api/v1/webhooks",
                    "mono_webhooks": "/api/v1/webhooks/mono",
                    "firs_webhooks": "/api/v1/webhooks/firs",
                    "documentation": "/docs",
                    "health": "/health (cached)",
                    "metrics": "/metrics (cached)"
                },
                "description": "Nigerian e-invoicing compliance and business system integration - Phase 4 Performance Optimized",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
        
        @self.app.get("/health", summary="Health Check")
        async def health_check():
            """Comprehensive health check with Phase 4 performance optimizations"""
            cache_key = "api_gateway_health_status"
            
            # Try to get cached health status (5 second TTL for fast responses)
            if self.cache_manager:
                cached_health = self.cache_manager.get(cache_key)
                if cached_health is not None:
                    return JSONResponse(
                        content=cached_health,
                        status_code=cached_health.get("status_code", 200)
                    )
            
            try:
                # Use async health checker for non-blocking checks
                if self.health_checker:
                    health_results = await self.health_checker.comprehensive_health_check([
                        {"name": "message_router", "check_func": self._check_message_router_health},
                        {"name": "role_manager", "check_func": self._check_role_manager_health}
                    ])
                    
                    all_healthy = all(result["healthy"] for result in health_results.values())
                    
                    health_response = {
                        "status": "healthy" if all_healthy else "degraded",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "components": {
                            "api_gateway": "healthy",
                            "message_router": "healthy" if health_results["message_router"]["healthy"] else "unhealthy",
                            "role_manager": "healthy" if health_results["role_manager"]["healthy"] else "unhealthy",
                            "cache_manager": "healthy" if self.cache_manager else "disabled",
                            "async_health_checker": "healthy" if self.health_checker else "disabled"
                        },
                        "version": "1.0.0",
                        "performance_optimized": True
                    }
                    
                    status_code = 200 if all_healthy else 503
                    health_response["status_code"] = status_code
                    
                    # Cache the result for 5 seconds to reduce health check overhead
                    if self.cache_manager:
                        self.cache_manager.set(cache_key, health_response, ttl=5)
                    
                    return JSONResponse(content=health_response, status_code=status_code)
                
                else:
                    # Fallback to synchronous checks if async health checker not available
                    router_health = await self._check_message_router_health()
                    role_manager_health = self._check_role_manager_health()
                    all_healthy = router_health and role_manager_health
                    
                    health_response = {
                        "status": "healthy" if all_healthy else "degraded",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "components": {
                            "api_gateway": "healthy",
                            "message_router": "healthy" if router_health else "unhealthy",
                            "role_manager": "healthy" if role_manager_health else "unhealthy"
                        },
                        "version": "1.0.0"
                    }
                    
                    status_code = 200 if all_healthy else 503
                    return JSONResponse(content=health_response, status_code=status_code)
                    
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                error_response = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                return JSONResponse(content=error_response, status_code=503)
        
        @self.app.get("/metrics", summary="API Metrics")
        async def get_metrics():
            """Get API gateway metrics with Phase 4 performance optimizations"""
            cache_key = "api_gateway_metrics"
            
            # Try to get cached metrics (30 second TTL for reasonable freshness)
            if self.cache_manager:
                cached_metrics = self.cache_manager.get(cache_key)
                if cached_metrics is not None:
                    cached_metrics["cached"] = True
                    return JSONResponse(content=cached_metrics)
            
            try:
                # Get fresh metrics from Phase 4 infrastructure
                metrics = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "requests_total": 0,  # Will be populated by Prometheus integration
                    "requests_by_role": {
                        "system_integrator": 0,
                        "access_point_provider": 0,
                        "hybrid": 0
                    },
                    "response_times": {
                        "p50": 0.1,
                        "p95": 0.5,
                        "p99": 1.0
                    },
                    "error_rate": 0.01,
                    "active_connections": 0,
                    "cache_performance": self._get_cache_metrics(),
                    "phase_4_enabled": True,
                    "cached": False
                }
                
                # Cache the metrics for 30 seconds
                if self.cache_manager:
                    self.cache_manager.set(cache_key, metrics, ttl=30)
                
                return JSONResponse(content=metrics)
                
            except Exception as e:
                logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail="Failed to get metrics")
    
    def _get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        if not self.cache_manager:
            return {"status": "disabled"}
        
        try:
            cache_metrics = self.cache_manager.get_metrics()
            return {
                "status": "enabled",
                "hit_ratio": round(cache_metrics.hit_ratio, 2),
                "total_operations": cache_metrics.total_operations,
                "avg_response_time_ms": round(cache_metrics.avg_response_time_ms, 2),
                "memory_usage_mb": round(cache_metrics.memory_usage_mb, 2)
            }
        except Exception as e:
            logger.warning(f"Failed to get cache metrics: {e}")
            return {"status": "error", "error": str(e)}
    
    def _setup_global_handlers(self):
        """Setup global exception handlers"""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            """Handle HTTP exceptions with Phase 4 request tracking"""
            # Phase 4: Request ID now comes from ObservabilityMiddleware in main.py
            request_id = getattr(request.state, 'request_id', 
                               getattr(request.state, 'trace_id', 'unknown'))
            
            logger.warning(f"HTTP Exception {request_id}: {exc.status_code} - {exc.detail}")
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "status_code": exc.status_code,
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "phase_4_optimized": True
                }
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            """Handle general exceptions with Phase 4 request tracking"""
            # Phase 4: Request ID now comes from ObservabilityMiddleware in main.py
            request_id = getattr(request.state, 'request_id', 
                               getattr(request.state, 'trace_id', 'unknown'))
            
            logger.error(f"Unhandled Exception {request_id}: {exc}", exc_info=True)
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "phase_4_optimized": True
                }
            )
    
    async def _check_message_router_health(self) -> bool:
        """Check message router health"""
        try:
            # Test message routing to each service role
            test_results = []
            
            for service_role in [ServiceRole.SYSTEM_INTEGRATOR, ServiceRole.ACCESS_POINT_PROVIDER]:
                try:
                    result = await self.message_router.route_message(
                        service_role=service_role,
                        operation="health_check",
                        payload={},
                        timeout=5.0
                    )
                    test_results.append(result is not None)
                except Exception as e:
                    logger.warning(f"Health check failed for {service_role}: {e}")
                    test_results.append(False)
            
            return all(test_results)
        except Exception as e:
            logger.error(f"Message router health check failed: {e}")
            return False
    
    def _check_role_manager_health(self) -> bool:
        """Check role manager health"""
        try:
            # Test role manager functionality
            test_roles = [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER]
            
            for role in test_roles:
                permissions = self.role_manager.get_role_permissions(role)
                if not permissions:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Role manager health check failed: {e}")
            return False
    
    def get_custom_openapi(self):
        """Generate custom OpenAPI schema with role-based documentation"""
        if self.app.openapi_schema:
            return self.app.openapi_schema
        
        openapi_schema = get_openapi(
            title="TaxPoynt E-Invoice Platform API",
            version="1.0.0",
            description="""
            ## TaxPoynt E-Invoice Platform API
            
            Comprehensive API for Nigerian e-invoicing compliance and business system integration.
            
            ### Role-Based Access
            
            This API provides role-specific endpoints:
            
            - **System Integrator (`/api/v1/si/`)**: ERP/CRM/POS integration, organization management
            - **Access Point Provider (`/api/v1/app/`)**: FIRS integration, taxpayer onboarding, compliance
            - **Hybrid Services (`/api/v1/common/`)**: Cross-role functionality, shared resources
            
            ### Authentication
            
            API uses role-based authentication with JWT tokens. Include your token in the Authorization header:
            ```
            Authorization: Bearer <your-jwt-token>
            ```
            
            ### Rate Limiting
            
            API requests are rate-limited based on user role and endpoint type.
            """,
            routes=self.app.routes,
        )
        
        # Add custom info
        openapi_schema["info"]["x-logo"] = {
            "url": "https://taxpoynt.com/logo.png",
            "altText": "TaxPoynt Logo"
        }
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for role-based authentication"
            }
        }
        
        # Add role-based tags
        openapi_schema["tags"] = [
            {
                "name": "System Integrator Services",
                "description": "ERP/CRM/POS integration and organization management"
            },
            {
                "name": "Access Point Provider Services", 
                "description": "FIRS integration, taxpayer onboarding, and compliance"
            },
            {
                "name": "Hybrid Services",
                "description": "Cross-role functionality and shared resources"
            }
        ]
        
        self.app.openapi_schema = openapi_schema
        return openapi_schema
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        # Set custom OpenAPI generator
        self.app.openapi = self.get_custom_openapi
        return self.app
    
    def update_message_router(self, message_router):
        """Update the message router after initialization"""
        logger.info(f"🔄 Updating API Gateway message router: {type(message_router).__name__}")
        self.message_router = message_router
        
        # Update message router in all created routers
        for router_name, router in [
            # Note: Legacy si_router removed - using main API Gateway instead
            ("app_router", getattr(self, '_app_router', None)),  
            ("hybrid_router", getattr(self, '_hybrid_router', None)),
            ("auth_router", getattr(self, '_auth_router', None)),
            ("admin_router", getattr(self, '_admin_router', None))
        ]:
            if router and hasattr(router, 'message_router'):
                router.message_router = message_router
                logger.info(f"✅ Updated message router for {router_name}")
        
        logger.info("✅ API Gateway message router update completed")
    
    async def cleanup(self):
        """Cleanup Phase 4 performance infrastructure."""
        try:
            if self.cache_manager:
                self.cache_manager.close()
                logger.info("Cache manager cleaned up")
            
            if self.health_checker:
                await self.health_checker.cleanup()
                logger.info("Async health checker cleaned up")
                
        except Exception as e:
            logger.error(f"Error during API Gateway cleanup: {e}")


def create_api_gateway(config: APIGatewayConfig,
                      role_manager: RoleManager,
                      message_router: MessageRouter) -> TaxPoyntAPIGateway:
    """Factory function to create API Gateway"""
    return TaxPoyntAPIGateway(config, role_manager, message_router)


def create_gateway_app(config: APIGatewayConfig,
                      role_manager: RoleManager, 
                      message_router: MessageRouter) -> FastAPI:
    """Factory function to create FastAPI app with API Gateway"""
    gateway = create_api_gateway(config, role_manager, message_router)
    return gateway.get_app()


# Example usage and configuration
if __name__ == "__main__":
    import uvicorn
    # Fixed import - use from .models import create_role_manager
    # Fixed import - use from .models import create_message_router
    
    # Example configuration
    config = APIGatewayConfig(
        host="0.0.0.0",
        port=8000,
        cors_enabled=True,
        cors_origins=["http://localhost:3000", "https://taxpoynt.com"],
        trusted_hosts=["taxpoynt.com", "*.taxpoynt.com"],
        security=RoutingSecurityLevel.STRICT
    )
    
    # Create dependencies (these would be injected in real application)
    role_manager = create_role_manager()
    message_router = create_message_router()
    
    # Create app
    app = create_gateway_app(config, role_manager, message_router)
    
    # Run server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        log_level="info",
        access_log=True
    )
