"""
TaxPoynt E-Invoice Platform Backend
==================================
Main application entry point with API Gateway architecture integration.

Phase 6 Enterprise Fault Tolerance Integration:
- ErrorCoordinator: Structured error handling with full context preservation
- RetryManager: Exponential backoff retry strategies for service initialization
- CircuitBreaker: Service failure protection with automatic recovery
- DeadLetterHandler: Failed operation recovery and replay capabilities
- GracefulDegradation: Service degradation modes for partial functionality
- RecoveryOrchestrator: Automated error recovery workflows
- IncidentTracker: Problem tracking and escalation management
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Environment configuration with Railway optimization
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = ENVIRONMENT == "development"
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
RAILWAY_DEPLOYMENT = os.getenv("RAILWAY_DEPLOYMENT_ID") is not None

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Health check middleware for robust startup detection
class HealthCheckMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.startup_time = datetime.now()
        self._health_manager = None
        
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            # Fast health response for Railway (non-blocking)
            base_health = {
                "status": "healthy",
                "service": "taxpoynt_platform_backend",
                "environment": ENVIRONMENT,
                "railway_deployment": RAILWAY_DEPLOYMENT,
                "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Add detailed health if manager is available (non-blocking)
            if self._health_manager:
                try:
                    # Get cached health status (non-blocking)
                    detailed_health = await asyncio.wait_for(
                        self._health_manager.get_health_status(),
                        timeout=0.1  # 100ms max
                    )
                    base_health["services"] = detailed_health.get("services", {})
                    base_health["overall_status"] = detailed_health.get("overall_status", "healthy")
                except asyncio.TimeoutError:
                    # Don't block if health check takes too long
                    base_health["services_status"] = "timeout"
                except Exception:
                    # Don't block on health check errors
                    base_health["services_status"] = "unavailable"
            
            return JSONResponse(base_health)
        
        return await call_next(request)
    
    def set_health_manager(self, health_manager):
        """Set health manager after initialization"""
        self._health_manager = health_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import API Gateway components
try:
    from api_gateway.role_routing.models import APIGatewayConfig, RoutingSecurityLevel
    from api_gateway.role_routing.gateway import TaxPoyntAPIGateway
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    from api_gateway.role_routing.permission_guard import APIPermissionGuard
    from api_gateway.role_routing.auth_router import create_auth_router
    
    # Core platform components (production ready)
    from core_platform.authentication.role_manager import RoleManager
    from core_platform.messaging.redis_message_router import get_redis_message_router, RedisMessageRouter
    from core_platform.messaging.message_router import ServiceRole
    
    # Phase 6: Enterprise Fault Tolerance Infrastructure
    from hybrid_services.error_management import (
        create_error_management_services,
        initialize_error_management_services,
        handle_platform_error,
        cleanup_error_management_services
    )
    from external_integrations.connector_framework.shared_utilities.retry_manager import (
        RetryManager, RetryConfig, RetryStrategy
    )
    from core_platform.messaging.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
    from core_platform.messaging.dead_letter_handler import DeadLetterHandler, FailureReason, RecoveryAction
    
    logger = logging.getLogger(__name__)
    logger.info("✅ Successfully imported TaxPoynt Production Architecture")
    
except ImportError as e:
    logger.error(f"❌ CRITICAL: Gateway components not available: {e}")
    logger.error(f"🔍 Import error details: {type(e).__name__}: {str(e)}")
    import traceback
    logger.error(f"📝 Full traceback:\n{traceback.format_exc()}")
    raise ImportError(f"Production components missing: {e}")

def create_role_manager():
    """Create and initialize role manager"""
    config = {
        'service_name': 'TaxPoynt_RoleManager',
        'environment': ENVIRONMENT,
        'log_level': 'INFO' if not DEBUG else 'DEBUG'
    }
    return RoleManager(config)

def get_service_degradation_mode(service_name: str, error: Exception) -> str:
    """Phase 6.3: Determine appropriate degradation mode for failed services"""
    degradation_modes = {
        "database": "continue_with_memory_cache",
        "production_messaging": "basic_http_routing",
        "production_observability": "basic_logging_only",
        "si_services": "direct_api_fallback",
        "app_services": "direct_firs_integration",
        "hybrid_services": "individual_service_calls"
    }
    
    return degradation_modes.get(service_name, "minimal_functionality")


async def handle_failed_operation(operation_name: str, operation_data: dict, error: Exception, failure_reason: FailureReason):
    """Phase 6.4: Send failed operations to dead letter queue for recovery"""
    if hasattr(app.state, 'dead_letter_handler') and app.state.dead_letter_handler:
        try:
            await app.state.dead_letter_handler.handle_dead_letter(
                operation_name=operation_name,
                original_payload=operation_data,
                failure_reason=failure_reason,
                error_details={
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "timestamp": datetime.now().isoformat()
                },
                recovery_action=RecoveryAction.RETRY,  # Default to retry
                max_retry_attempts=3
            )
            logger.info(f"📨 Failed operation '{operation_name}' sent to dead letter queue")
        except Exception as dlq_error:
            logger.error(f"❌ Failed to send operation to dead letter queue: {dlq_error}")
    else:
        logger.warning(f"⚠️  Dead letter queue unavailable, operation '{operation_name}' lost")


async def create_production_messaging():
    """Create and initialize production messaging infrastructure with Phase 6 circuit breaker"""  
    from core_platform.messaging import initialize_production_messaging_infrastructure
    
    # Phase 6: Circuit breaker protection for external service calls
    circuit_breaker_config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        success_threshold=2
    )
    messaging_circuit_breaker = CircuitBreaker("messaging_infrastructure", circuit_breaker_config)
    
    return await messaging_circuit_breaker.call_async(
        initialize_production_messaging_infrastructure
    )

def create_taxpoynt_app() -> FastAPI:
    """Create TaxPoynt application with production architecture"""
    
    # Use production API gateway architecture
    logger.info("🚀 Initializing TaxPoynt Platform with Production Architecture")
    
    # Create gateway configuration
    allowed_origins = [
        "https://web-production-ea5ad.up.railway.app",  # Railway production
        "https://app-staging.taxpoynt.com",
        "https://app.taxpoynt.com",
        "https://taxpoynt.com",  # Main domain
        "https://www.taxpoynt.com",  # WWW subdomain
        "http://localhost:3000",
        "http://localhost:3001"  # Frontend dev port
    ] if not DEBUG else ["*"]
    
    # Initialize secure JWT manager (no hardcoded secrets)
    from core_platform.security import initialize_jwt_manager, get_jwt_manager
    from core_platform.security.rate_limiter import initialize_rate_limiter, rate_limit_middleware
    from core_platform.security.security_headers import initialize_security_headers, security_headers_middleware
    
    jwt_manager = initialize_jwt_manager()
    rate_limiter = initialize_rate_limiter()
    security_headers = initialize_security_headers()
    
    config = APIGatewayConfig(
        host="0.0.0.0",
        port=PORT,
        cors_enabled=True,
        cors_origins=allowed_origins,
        trusted_hosts=None,  # Disable for production - Railway handles host validation
        security=RoutingSecurityLevel.STANDARD,
        jwt_secret_key="SECURE_JWT_MANAGED_BY_JWT_MANAGER",  # Placeholder - actual security handled by JWT Manager
        jwt_expiration_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),  # Reduced from 1440 to 60 minutes
        enable_request_logging=True,
        enable_metrics=True,
        log_level="INFO" if not DEBUG else "DEBUG"
    )
    
    # Create core platform components
    role_manager = create_role_manager()
    
    # Create temporary message router for gateway initialization
    # (will be replaced with production messaging in startup)
    from core_platform.messaging import get_redis_message_router
    temp_message_router = get_redis_message_router()
    
    # Create API gateway
    gateway = TaxPoyntAPIGateway(config, role_manager, temp_message_router)
    app = gateway.get_app()
    
    # CRITICAL: Add CORS middleware FIRST to handle preflight requests properly
    # This ensures CORS headers are added before any other middleware can interfere
    from fastapi.middleware.cors import CORSMiddleware
    
    logger.info(f"🌐 CORS Configuration - Allowed Origins: {allowed_origins}")
    logger.info(f"🔄 CORS Debug Mode: {DEBUG}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining", "X-Total-Count"],
        max_age=86400  # Cache preflight requests for 24 hours
    )
    
    # Add health check middleware 
    app.add_middleware(HealthCheckMiddleware)
    
    # Add observability middleware (Phase 4)
    from core_platform.monitoring.fastapi_middleware import ObservabilityMiddleware
    app.add_middleware(
        ObservabilityMiddleware,
        collect_metrics=True,
        collect_traces=True,
        track_business_operations=True
    )
    
    # Add OWASP security headers middleware (critical security)
    app.middleware("http")(security_headers_middleware)
    
    # Add rate limiting middleware (critical security)
    app.middleware("http")(rate_limit_middleware)
    
    logger.info("✅ TaxPoynt Platform initialized with Phase 4 Production Architecture")
    logger.info("   🔐 Security: JWT, Rate Limiting, OWASP Headers, Circuit Breakers")
    logger.info("   🚀 Scaling: Redis Routing, Horizontal Coordinator, Auto-scaling")
    logger.info("   📊 Observability: Prometheus Metrics, OpenTelemetry Tracing")
    logger.info("   💓 Monitoring: Async Health Checks, Business Metrics")
    return app

# Create the app instance
app = create_taxpoynt_app()

async def initialize_services():
    """Initialize core platform services with Phase 6 fault tolerance"""
    try:
        # Phase 6: Initialize Enterprise Error Management Infrastructure First
        logger.info("🛡️ Initializing Phase 6 Enterprise Error Management...")
        try:
            error_management_services = create_error_management_services()
            await initialize_error_management_services(error_management_services)
            
            # Store in app state for use throughout platform
            app.state.error_management = error_management_services
            
            logger.info("✅ Phase 6 Enterprise Error Management initialized")
            logger.info("   🎯 ErrorCoordinator: Structured error handling")
            logger.info("   🔄 RecoveryOrchestrator: Automated recovery workflows")
            logger.info("   📈 EscalationManager: Incident escalation")
            logger.info("   📤 NotificationRouter: Alert routing")
            logger.info("   📋 IncidentTracker: Problem tracking")
            
        except Exception as e:
            # Use basic error handling since error management isn't ready yet
            logger.error(f"❌ Failed to initialize error management: {e}")
            app.state.error_management = None
        
        # Initialize retry manager for robust service initialization
        retry_config = RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            initial_delay_seconds=1.0,
            max_delay_seconds=60.0,
            enable_jitter=True
        )
        app.state.service_retry_manager = RetryManager(retry_config)
        
        # Initialize dead letter queue for failed operations (Phase 6.4)
        try:
            app.state.dead_letter_handler = DeadLetterHandler()
            await app.state.dead_letter_handler.initialize()
            logger.info("✅ Phase 6 Dead Letter Queue initialized for operation recovery")
        except Exception as e:
            logger.warning(f"⚠️  Dead Letter Queue initialization failed: {e}")
            app.state.dead_letter_handler = None
        # Initialize production database with optimizations and Phase 6 fault tolerance
        logger.info("🗃️  Initializing production database...")
        
        @app.state.service_retry_manager.retry_async(
            operation_name="database_initialization",
            context={"service": "database", "operation": "initialization"}
        )
        async def initialize_database_with_retry():
            from core_platform.data_management.database_init import initialize_database
            return await initialize_database()
        
        try:
            database = await initialize_database_with_retry()
            app.state.database = database
            logger.info("✅ Production database initialized with optimizations")
        except Exception as e:
            # Phase 6: Structured error handling with context preservation
            if app.state.error_management:
                await handle_platform_error(
                    app.state.error_management, e, {
                        "service_name": "database",
                        "operation_name": "initialization",
                        "severity": "high",
                        "user_id": None,
                        "request_id": None,
                        "retry_attempts": 3,
                        "degradation_mode": "continue_without_db_optimizations"
                    }, "system", "high"
                )
            else:
                logger.error(f"❌ Database initialization failed: {e}")
            
            # Continue - some services might still work without full DB optimization
            app.state.database = None
        
        # Initialize production messaging infrastructure (Phase 3) with Phase 6 fault tolerance
        logger.info("🚀 Initializing Phase 3 Production Messaging Infrastructure...")
        
        @app.state.service_retry_manager.retry_async(
            operation_name="messaging_infrastructure_initialization",
            context={"service": "messaging", "operation": "initialization", "phase": "3"}
        )
        async def initialize_messaging_with_retry():
            return await create_production_messaging()
        
        try:
            messaging_infrastructure = await initialize_messaging_with_retry()
            
            # Store in app state
            app.state.messaging = messaging_infrastructure
            app.state.redis_message_router = messaging_infrastructure["redis_message_router"]
            app.state.scaling_coordinator = messaging_infrastructure["scaling_coordinator"]
            app.state.circuit_breaker_manager = messaging_infrastructure["circuit_breaker_manager"]
            app.state.health_check_manager = messaging_infrastructure["health_check_manager"]
            
            # Set health manager in middleware
            for middleware in app.user_middleware:
                if hasattr(middleware, 'cls') and middleware.cls.__name__ == 'HealthCheckMiddleware':
                    if hasattr(middleware, 'kwargs') and 'app' in middleware.kwargs:
                        health_middleware = middleware.kwargs['app']
                        if hasattr(health_middleware, 'set_health_manager'):
                            health_middleware.set_health_manager(messaging_infrastructure["health_check_manager"])
            
            logger.info("✅ Phase 3 Production Messaging Infrastructure initialized")
            logger.info(f"   📍 Redis Message Router: Distributed state management")
            logger.info(f"   📊 Scaling Coordinator: Auto-scaling for 1M+ transactions")
            logger.info(f"   🔒 Circuit Breaker: Service failure protection")
            logger.info(f"   💓 Health Monitor: Non-blocking health checks")
            
        except Exception as e:
            # Phase 6: Enhanced error handling with recovery orchestration
            if app.state.error_management:
                await handle_platform_error(
                    app.state.error_management, e, {
                        "service_name": "production_messaging",
                        "operation_name": "infrastructure_initialization",
                        "severity": "critical",  # Messaging is critical for platform
                        "user_id": None,
                        "request_id": None,
                        "retry_attempts": 3,
                        "degradation_mode": "basic_messaging_functionality",
                        "recovery_strategy": "exponential_backoff",
                        "phase": "3"
                    }, "infrastructure", "critical"
                )
            else:
                logger.error(f"❌ Failed to initialize production messaging: {e}")
            
            # Initialize basic messaging as fallback
            app.state.messaging = None
            logger.warning("⚠️  Operating with basic messaging functionality")
        
        # Initialize Phase 4 Production Observability
        logger.info("📊 Initializing Phase 4 Production Observability...")
        try:
            from core_platform.monitoring import setup_production_observability
            
            await setup_production_observability(
                enable_prometheus=True,
                prometheus_port=9090,
                enable_opentelemetry=True,
                service_name="taxpoynt-platform"
            )
            
            # Store observability components in app state
            from core_platform.monitoring import get_prometheus_integration, get_opentelemetry_integration
            app.state.prometheus_integration = get_prometheus_integration()
            app.state.opentelemetry_integration = get_opentelemetry_integration()
            
            logger.info("✅ Phase 4 Production Observability initialized")
            logger.info(f"   📈 Prometheus Metrics: http://localhost:9090/metrics")
            logger.info(f"   🔍 Distributed Tracing: Jaeger/OTLP ready")
            logger.info(f"   💡 Business Metrics: E-invoicing, FIRS, Banking operations")
            
        except Exception as e:
            # Phase 6: Structured error handling for observability
            if app.state.error_management:
                await handle_platform_error(
                    app.state.error_management, e, {
                        "service_name": "production_observability",
                        "operation_name": "phase4_initialization",
                        "severity": "high",  # Observability is important but not critical
                        "user_id": None,
                        "request_id": None,
                        "retry_attempts": 3,
                        "degradation_mode": "basic_observability",
                        "recovery_strategy": "exponential_backoff",
                        "phase": "4"
                    }, "infrastructure", "high"
                )
            else:
                logger.error(f"❌ Failed to initialize production observability: {e}")
            
            # Continue without advanced observability but log the degradation
            logger.warning("⚠️  Operating without advanced observability features")
        
        # Initialize role manager
        if hasattr(app.state, 'role_manager') and app.state.role_manager:
            await app.state.role_manager.initialize()
            logger.info("✅ Role Manager initialized")
        
        # Initialize AI service with real OpenAI integration
        logger.info("🤖 Initializing AI Service with OpenAI integration...")
        try:
            from core_platform.ai import AIService, AIConfig, AIProvider
            
            # Create AI config with environment variables
            ai_config = AIConfig(
                provider=AIProvider.OPENAI,
                api_key=os.getenv("OPENAI_API_KEY"),
                model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),  # Cost-effective default
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                mock_responses=False  # Enable real OpenAI integration
            )
            
            # Initialize AI service
            ai_service = AIService(ai_config)
            ai_initialized = await ai_service.initialize()
            
            if ai_initialized:
                app.state.ai_service = ai_service
                logger.info(f"✅ AI Service initialized successfully - Provider: {ai_config.provider.value}, Model: {ai_config.model_name}")
                logger.info(f"   🧠 Available capabilities: {len(ai_service.get_capabilities())} AI features")
            else:
                logger.warning("⚠️  AI Service initialization failed - falling back to mock mode")
                app.state.ai_service = None
                
        except Exception as e:
            # Phase 6: AI service error handling
            if app.state.error_management:
                await handle_platform_error(
                    app.state.error_management, e, {
                        "service_name": "ai_service",
                        "operation_name": "initialization",
                        "severity": "medium",  # AI is important but not critical for core functionality
                        "user_id": None,
                        "request_id": None,
                        "retry_attempts": 2,
                        "degradation_mode": "continue_without_ai_features"
                    }, "ai_service", "medium"
                )
            else:
                logger.error(f"❌ Failed to initialize AI service: {e}")
            
            # Continue without AI features
            app.state.ai_service = None
            logger.warning("⚠️  Operating without AI features")
            
        # Register services with Redis message router
        if hasattr(app.state, 'redis_message_router') and app.state.redis_message_router:
            logger.info("🔄 Registering platform services with Redis Message Router...")
            
            # Register SI services
            try:
                from si_services import initialize_si_services
                si_registry = await initialize_si_services(app.state.redis_message_router)
                logger.info(f"✅ SI Services registered: {len(si_registry.service_endpoints)} services")
            except Exception as e:
                # Phase 6: Service registration error handling
                if app.state.error_management:
                    await handle_platform_error(
                        app.state.error_management, e, {
                            "service_name": "si_services",
                            "operation_name": "service_registration",
                            "severity": "medium",
                            "user_id": None,
                            "request_id": None,
                            "retry_attempts": 2,
                            "degradation_mode": "continue_without_si_services"
                        }, "service_registration", "medium"
                    )
                else:
                    logger.error(f"❌ Failed to register SI services: {e}")
            
            # Register APP services  
            try:
                from app_services import initialize_app_services
                app_registry = await initialize_app_services(app.state.redis_message_router)
                logger.info(f"✅ APP Services registered: {len(app_registry.service_endpoints)} services")
            except Exception as e:
                # Phase 6: Service registration error handling
                if app.state.error_management:
                    await handle_platform_error(
                        app.state.error_management, e, {
                            "service_name": "app_services",
                            "operation_name": "service_registration",
                            "severity": "medium",
                            "user_id": None,
                            "request_id": None,
                            "retry_attempts": 2,
                            "degradation_mode": "continue_without_app_services"
                        }, "service_registration", "medium"
                    )
                else:
                    logger.error(f"❌ Failed to register APP services: {e}")
            
            # Register Hybrid services
            try:
                from hybrid_services import initialize_hybrid_services
                hybrid_registry = await initialize_hybrid_services(app.state.redis_message_router)
                logger.info(f"✅ Hybrid Services registered: {len(hybrid_registry.service_endpoints)} services")
            except Exception as e:
                # Phase 6: Service registration error handling
                if app.state.error_management:
                    await handle_platform_error(
                        app.state.error_management, e, {
                            "service_name": "hybrid_services",
                            "operation_name": "service_registration",
                            "severity": "medium",
                            "user_id": None,
                            "request_id": None,
                            "retry_attempts": 2,
                            "degradation_mode": "continue_without_hybrid_services"
                        }, "service_registration", "medium"
                    )
                else:
                    logger.error(f"❌ Failed to register Hybrid services: {e}")
        
        logger.info("🎯 All Phase 4 Production Services initialized successfully")
        logger.info("🛡️  Phase 6 Enterprise Fault Tolerance: ACTIVE")
        
    except Exception as e:
        # Phase 6: Top-level error handling with full context
        if hasattr(app.state, 'error_management') and app.state.error_management:
            await handle_platform_error(
                app.state.error_management, e, {
                    "service_name": "platform",
                    "operation_name": "complete_initialization",
                    "severity": "critical",
                    "user_id": None,
                    "request_id": None,
                    "error_location": "main.initialize_services",
                    "platform_state": "initialization_failure"
                }, "platform", "critical"
            )
        else:
            logger.error(f"❌ Failed to initialize services: {e}")
        raise

async def cleanup_services():
    """Cleanup core platform services"""
    try:
        # Cleanup all service registries
        try:
            from si_services import cleanup_si_services
            await cleanup_si_services()
            logger.info("✅ SI Services cleaned up")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup SI services: {e}")
        
        try:
            from app_services import cleanup_app_services
            await cleanup_app_services()
            logger.info("✅ APP Services cleaned up")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup APP services: {e}")
            
        try:
            from hybrid_services import cleanup_hybrid_services
            await cleanup_hybrid_services()
            logger.info("✅ Hybrid Services cleaned up")
        except Exception as e:
            logger.error(f"❌ Failed to cleanup Hybrid services: {e}")
        
        # Cleanup role manager
        if hasattr(app.state, 'role_manager') and app.state.role_manager:
            await app.state.role_manager.cleanup()
            logger.info("✅ Role Manager cleaned up")
        
        # Cleanup Phase 3 messaging infrastructure
        if hasattr(app.state, 'messaging'):
            try:
                # Shutdown health monitoring
                if hasattr(app.state, 'health_check_manager'):
                    await app.state.health_check_manager.stop_all_monitoring()
                    logger.info("✅ Health Check Manager stopped")
                
                # Shutdown scaling coordinator
                if hasattr(app.state, 'scaling_coordinator'):
                    await app.state.scaling_coordinator.shutdown()
                    logger.info("✅ Scaling Coordinator shutdown")
                
                # Shutdown Redis message router
                if hasattr(app.state, 'redis_message_router'):
                    await app.state.redis_message_router.shutdown()
                    logger.info("✅ Redis Message Router shutdown")
                
            except Exception as e:
                logger.error(f"❌ Failed to cleanup messaging infrastructure: {e}")
        
        # Cleanup Phase 4 observability
        if hasattr(app.state, 'prometheus_integration') or hasattr(app.state, 'opentelemetry_integration'):
            try:
                from core_platform.monitoring import shutdown_platform_observability
                await shutdown_platform_observability()
                logger.info("✅ Phase 4 Production Observability shutdown")
            except Exception as e:
                logger.error(f"❌ Failed to cleanup observability: {e}")
        
        # Cleanup Phase 6 Error Management Services (last to ensure error handling until the end)
        if hasattr(app.state, 'error_management') and app.state.error_management:
            try:
                await cleanup_error_management_services(app.state.error_management)
                logger.info("✅ Phase 6 Enterprise Error Management shutdown")
            except Exception as e:
                logger.error(f"❌ Failed to cleanup error management: {e}")
        
        logger.info("🎯 All Phase 4 & 6 Production Services cleaned up successfully") 
    except Exception as e:
        # Final error handling - basic logging since error management is shutting down
        logger.error(f"❌ Failed to cleanup services: {e}")

# Add startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🚀 TaxPoynt Platform Backend starting up...")
    logger.info(f"📊 Environment: {ENVIRONMENT}")
    logger.info(f"🚂 Railway Deployment: {RAILWAY_DEPLOYMENT}")
    logger.info(f"🌐 Port: {PORT}")
    
    logger.info("✅ Phase 4 Production Platform: ENABLED")
    logger.info("🔐 Security Layer: JWT, Rate Limiting, OWASP Headers, Circuit Breakers")
    logger.info("🚀 Scaling Layer: Redis Routing, Horizontal Coordinator, Auto-scaling")
    logger.info("📊 Observability Layer: Prometheus Metrics, OpenTelemetry Tracing")
    logger.info("🎯 Business Features: E-invoicing, FIRS integration, Banking, Compliance")
    await initialize_services()
    
    logger.info("==================================================")
    logger.info("🎉 TAXPOYNT PLATFORM STARTUP SUCCESS")
    logger.info(f"⚡ Environment: {ENVIRONMENT}")
    logger.info("🔗 Health Check: /health")
    logger.info(f"📚 API Docs: /docs {'(enabled)' if DEBUG else '(disabled)'}")
    logger.info("==================================================")

@app.on_event("shutdown") 
async def shutdown_event():
    """Application shutdown"""
    logger.info("👋 TaxPoynt Platform Backend shutting down...")
    await cleanup_services()

# FIRS endpoints are now handled by the API Gateway APP router

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="info",
        access_log=True,
        reload=DEBUG
    )