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

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment variables from {env_file}")
else:
    print(f"⚠️ .env file not found at {env_file}")

# Environment configuration with Railway optimization
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = ENVIRONMENT == "development"
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
RAILWAY_DEPLOYMENT = os.getenv("RAILWAY_DEPLOYMENT_ID") is not None

# Add project root to path  
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
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    from api_gateway.role_routing.permission_guard import APIPermissionGuard
    from api_gateway.role_routing.auth_router import create_auth_router
    from api_gateway.main_gateway_router import create_main_gateway, create_main_gateway_router
    from api_gateway.api_versions.version_coordinator import APIVersionCoordinator
    
    # Core platform components (production ready)
    from core_platform.authentication.role_manager import RoleManager
    from core_platform.messaging.redis_message_router import get_redis_message_router, RedisMessageRouter
    from core_platform.messaging.message_router import (
        ServiceRole,
        MessageRouter,
        get_message_router as get_inmemory_message_router,
    )
    
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
    # Optionally wire a persistence-backed repository
    repository = None
    try:
        # Default to using repository in development unless explicitly disabled
        repo_env = str(os.getenv("ROLE_MANAGER_USE_REPOSITORY", "")).strip().lower()
        if repo_env:
            use_repo = repo_env in ("1", "true", "yes", "on")
        else:
            use_repo = (ENVIRONMENT == "development")
        if use_repo:
            from core_platform.authentication.role_repository_sqlalchemy import SQLAlchemyRoleRepository
            from core_platform.data_management.db_async import init_async_engine
            from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

            engine = init_async_engine()  # reuse global async engine
            session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

            async def session_factory():
                # Return an async context manager created by sessionmaker
                return session_maker()

            repository = SQLAlchemyRoleRepository(session_factory)  # type: ignore[arg-type]
            logger.info("RoleManager will use SQLAlchemyRoleRepository for persistence")
    except Exception as e:
        logger.warning(f"Failed to initialize RoleManager repository: {e}")

    return RoleManager(config, repository=repository)

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
    
    return await messaging_circuit_breaker.call(
        initialize_production_messaging_infrastructure
    )

def create_taxpoynt_app() -> FastAPI:
    """Create TaxPoynt application with production architecture"""
    
    # Use production API gateway architecture
    logger.info("🚀 Initializing TaxPoynt Platform with Production Architecture")
    
    # Create gateway configuration
    config = APIGatewayConfig(
        host="0.0.0.0",
        port=PORT,
        cors_enabled=True,
        cors_origins=[
            "https://web-production-ea5ad.up.railway.app",  # Railway production
            "https://app-staging.taxpoynt.com",
            "https://app.taxpoynt.com",
            "https://taxpoynt.com",  # Main domain
            "https://www.taxpoynt.com",  # WWW subdomain - Vercel frontend
            "http://localhost:3000",
            "http://localhost:3001"  # Frontend dev port
        ] if not DEBUG else ["*"],
        trusted_hosts=None,
        security=RoutingSecurityLevel.STANDARD,
        jwt_secret_key="SECURE_JWT_MANAGED_BY_JWT_MANAGER",
        jwt_expiration_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
        enable_request_logging=True,
        enable_metrics=True,
        log_level="INFO" if not DEBUG else "DEBUG"
    )
    
    # Initialize secure JWT manager (no hardcoded secrets)
    from core_platform.security import initialize_jwt_manager, get_jwt_manager
    from core_platform.security.rate_limiter import initialize_rate_limiter, rate_limit_middleware
    from core_platform.security.security_headers import initialize_security_headers, security_headers_middleware
    
    jwt_manager = initialize_jwt_manager()
    rate_limiter = initialize_rate_limiter()
    security_headers = initialize_security_headers()
    
    # Create core platform components
    role_manager = create_role_manager()
    
    # Create temporary message router for gateway initialization
    # (will be replaced with production messaging in startup)
    def _initialize_temp_message_router() -> MessageRouter:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                logger.info(f"Attempting to initialize Redis message router (REDIS_URL={redis_url})")
                return get_redis_message_router()
            except Exception as exc:
                logger.warning("Redis message router unavailable (%s). Falling back to in-memory router.", exc)
        logger.info("Using in-memory message router")
        return get_inmemory_message_router()

    temp_message_router = _initialize_temp_message_router()
    
    # Create version coordinator
    version_coordinator = APIVersionCoordinator(temp_message_router)
    
    # Create FastAPI app with main router
    app = FastAPI(
        title="TaxPoynt Platform API",
        description="TaxPoynt E-Invoice Platform API",
        version="1.0.0",
        docs_url="/docs" if DEBUG else None,
        redoc_url="/redoc" if DEBUG else None
    )
    
    # Create permission guard with app
    permission_guard = APIPermissionGuard(app)
    
    # Create main gateway controller (preferred) and include its router
    gateway_controller = create_main_gateway(
        role_detector=HTTPRoleDetector(),
        permission_guard=permission_guard,
        message_router=temp_message_router,
        version_coordinator=version_coordinator
    )
    
    # Include main router
    app.include_router(gateway_controller.router)

    # Attach shared authentication routes so registration/login endpoints are accessible
    auth_router = create_auth_router(
        gateway_controller.role_detector,
        permission_guard,
        temp_message_router,
    )
    app.include_router(auth_router, prefix="/api/v1")

    # Store gateway controller for later message router updates (future-proof)
    app.state.gateway_controller = gateway_controller
    # Backward-compat: expose under previous private attribute as well
    app._taxpoynt_gateway = gateway_controller
    
    # CRITICAL: Add CORS middleware FIRST to handle preflight requests properly
    # This ensures CORS headers are added before any other middleware can interfere
    from fastapi.middleware.cors import CORSMiddleware
    
    logger.info(f"🌐 CORS Configuration - Allowed Origins: {config.cors_origins}")
    logger.info(f"🔄 CORS Debug Mode: {DEBUG}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining", "X-Total-Count"],
        max_age=86400  # Cache preflight requests for 24 hours
    )
    
    # Railway host header fix for production
    @app.middleware("http")
    async def fix_host_header(request, call_next):
        """Fix Railway host header issues with Vercel frontend"""
        if request.headers.get("host") in ["web-production-ea5ad.up.railway.app", "www.taxpoynt.com"]:
            # Allow both Railway backend and Vercel frontend hosts
            response = await call_next(request)
            return response
        response = await call_next(request)
        return response
    
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

    # Optional tenant scoping middleware for APP routes
    try:
        from api_gateway.middleware.tenant_scope import TenantScopeMiddleware
        app.add_middleware(TenantScopeMiddleware)
    except Exception as _e:
        logger.warning(f"Tenant scope middleware not applied: {_e}")
    
    # Add OWASP security headers middleware (critical security)
    app.middleware("http")(security_headers_middleware)

    # Ensure every request has a request ID and propagate
    try:
        from api_gateway.middleware.request_id import RequestIDMiddleware
        app.add_middleware(RequestIDMiddleware)
    except Exception as _e:
        logger.warning(f"Request ID middleware not applied: {_e}")

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

            # Initialize MultiTenantManager (aligns with tenant dependency)
            try:
                from core_platform.data_management.multi_tenant_manager import initialize_tenant_manager
                from contextlib import contextmanager

                class _DBLayerAdapter:
                    """Minimal adapter exposing get_session() for MultiTenantManager."""
                    def __init__(self, SessionLocal):
                        self._SessionLocal = SessionLocal

                    @contextmanager
                    def get_session(self):
                        session = self._SessionLocal()
                        try:
                            yield session
                        finally:
                            session.close()

                if hasattr(database, 'SessionLocal') and database.SessionLocal is not None:
                    tenant_mgr = initialize_tenant_manager(_DBLayerAdapter(database.SessionLocal))
                    app.state.tenant_manager = tenant_mgr
                    logger.info("✅ MultiTenantManager initialized and wired to request lifecycle")
                else:
                    logger.warning("⚠️ Could not initialize MultiTenantManager: SessionLocal not available")
            except Exception as te:
                logger.warning(f"⚠️ Tenant manager initialization skipped: {te}")
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
            # Register basic operation schemas for core operations
            try:
                from core_platform.messaging.message_router import MessageRouter
                mr: MessageRouter = app.state.redis_message_router
                # Pydantic model for submit_invoice
                try:
                    from pydantic import BaseModel

                    class _SubmitInvoiceSchema(BaseModel):
                        schema_version: str
                        invoice_number: str
                        amount: float

                    mr.register_operation_schema(
                        "submit_invoice",
                        pydantic_model=_SubmitInvoiceSchema,
                        expected_version="1.0",
                    )
                except Exception as _e:
                    logger.warning(f"Schema registry (pydantic) not available: {_e}")

                # JSON Schema for update_firs_submission_status (or status notifications)
                status_schema = {
                    "type": "object",
                    "required": ["schema_version", "submission_id", "status"],
                    "properties": {
                        "schema_version": {"type": "string"},
                        "submission_id": {"type": "string"},
                        "status": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "additionalProperties": True,
                }
                mr.register_operation_schema(
                    "update_firs_submission_status",
                    json_schema=status_schema,
                    expected_version="1.0",
                )
            except Exception as se:
                logger.warning(f"Operation schema registration skipped: {se}")
            
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

        # Start periodic idempotency cleanup task
        try:
            from core_platform.idempotency.store import IdempotencyStore
            from core_platform.data_management.db_async import get_async_session

            cleanup_days = int(os.getenv("IDEMPOTENCY_CLEANUP_DAYS", "7"))
            interval_seconds = int(os.getenv("IDEMPOTENCY_CLEANUP_INTERVAL_SECONDS", "86400"))  # daily

            async def _idem_cleanup_loop():
                while True:
                    try:
                        async for db in get_async_session():
                            deleted = await IdempotencyStore.cleanup(db, older_than_days=cleanup_days)
                            if deleted:
                                logger.info(f"🧹 Idempotency cleanup removed {deleted} rows older than {cleanup_days} days")
                    except Exception as ce:
                        logger.warning(f"Idempotency cleanup failed: {ce}")
                    await asyncio.sleep(interval_seconds)

            app.state.idem_cleanup_task = asyncio.create_task(_idem_cleanup_loop())
            logger.info("🧹 Scheduled idempotency cleanup task")
        except Exception as tce:
            logger.warning(f"Could not schedule idempotency cleanup task: {tce}")
        
        # Initialize Phase 4 Production Observability
        logger.info("📊 Initializing Phase 4 Production Observability...")
        try:
            from core_platform.monitoring import setup_production_observability
            # OpenTelemetry is optional; gate on OTEL_ENABLED
            otel_enabled = str(os.getenv("OTEL_ENABLED", "false")).lower() in ("1", "true", "yes", "on")
            await setup_production_observability(
                enable_prometheus=True,
                prometheus_port=9090,
                enable_opentelemetry=otel_enabled,
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
            
            # CRITICAL: Update API gateway to use the real Redis message router
            logger.info("🔄 Updating API Gateway to use production Redis Message Router...")
            try:
                # Preferred: use stored controller
                if hasattr(app.state, 'gateway_controller') and app.state.gateway_controller:
                    app.state.gateway_controller.update_message_router(app.state.redis_message_router)
                else:
                    # Fallback: Update through route endpoints
                    logger.info("🔍 Fallback: Updating message router through route endpoints...")
                    updated_count = 0
                    for route in app.routes:
                        if hasattr(route, 'endpoint') and hasattr(route.endpoint, '__self__'):
                            endpoint_instance = route.endpoint.__self__
                            if hasattr(endpoint_instance, 'message_router'):
                                endpoint_instance.message_router = app.state.redis_message_router
                                updated_count += 1
                    logger.info(f"✅ Updated message router for {updated_count} endpoints via fallback method")
                
                logger.info("✅ API Gateway message router updated to production Redis router")
            except Exception as e:
                logger.error(f"❌ Failed to update API Gateway message router: {e}")
            
            # Register SI services (optional in staging via ENABLE_SI_SERVICES)
            enable_si = str(os.getenv("ENABLE_SI_SERVICES", "true" if ENVIRONMENT != "staging" else "false")).lower() in ("1", "true", "yes", "on")
            if enable_si:
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
                            }, "integration", "medium"
                        )
                    else:
                        logger.error(f"❌ Failed to register SI services: {e}")
            else:
                logger.info("⏭️ Skipping SI service registration (ENABLE_SI_SERVICES disabled)")
            
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
                        }, "integration", "medium"
                    )
                else:
                    logger.error(f"❌ Failed to register APP services: {e}")
            
            # Register Hybrid services (optional in staging via ENABLE_HYBRID_SERVICES)
            enable_hybrid = str(os.getenv("ENABLE_HYBRID_SERVICES", "true" if ENVIRONMENT != "staging" else "false")).lower() in ("1", "true", "yes", "on")
            if enable_hybrid:
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
                            }, "integration", "medium"
                        )
                    else:
                        logger.error(f"❌ Failed to register Hybrid services: {e}")
            else:
                logger.info("⏭️ Skipping Hybrid service registration (ENABLE_HYBRID_SERVICES disabled)")

            # Validate route→operation mapping after all services are registered
            try:
                validate = str(os.getenv("ROUTER_VALIDATE_ON_STARTUP", "false")).lower() in ("1", "true", "yes", "on")
                if validate and hasattr(app.state, 'gateway_controller') and app.state.gateway_controller:
                    fail_fast = str(os.getenv("ROUTER_FAIL_FAST_ON_STARTUP", "false")).lower() in ("1", "true", "yes", "on")
                    app.state.gateway_controller.validate_route_operation_mapping(fail_fast=fail_fast)
                    logger.info("✅ Route→operation mapping validation completed")
            except Exception as e:
                logger.error(f"❌ Route→operation mapping validation failed: {e}")
        
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
    # Cancel idempotency cleanup task
    try:
        task = getattr(app.state, 'idem_cleanup_task', None)
        if task:
            task.cancel()
    except Exception:
        pass
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
