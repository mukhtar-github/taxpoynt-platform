"""
TaxPoynt Platform Backend - Main Application Entry Point
========================================================
Enterprise FastAPI application with microservices architecture.
Bootstraps the API Gateway with role-based routing and version management.
"""
import os
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# Core platform imports
from core_platform.authentication.role_manager import PlatformRoleManager
from core_platform.messaging.message_router import MessageRouter
from core_platform.monitoring.health_orchestrator import HealthOrchestrator

# API Gateway imports
from api_gateway.main_gateway_router import create_main_gateway_router
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.api_versions.version_coordinator import APIVersionCoordinator
from api_gateway.middleware.stack import create_middleware_stack

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("PORT", "8000"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 TaxPoynt Platform Backend starting up...")
    
    # Initialize core services
    await initialize_core_services()
    
    logger.info("✅ TaxPoynt Platform Backend ready!")
    
    yield
    
    # Shutdown
    logger.info("⏳ TaxPoynt Platform Backend shutting down...")
    await cleanup_services()
    logger.info("✅ TaxPoynt Platform Backend shutdown complete!")


async def initialize_core_services():
    """Initialize core platform services"""
    try:
        # Initialize role management
        role_manager = PlatformRoleManager()
        
        # Initialize message routing
        message_router = MessageRouter()
        
        # Initialize health monitoring
        health_orchestrator = HealthOrchestrator()
        
        # Store in app state for access by routes
        app.state.role_manager = role_manager
        app.state.message_router = message_router
        app.state.health_orchestrator = health_orchestrator
        
        logger.info("Core services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize core services: {e}")
        raise


async def cleanup_services():
    """Cleanup services on shutdown"""
    try:
        # Cleanup message router
        if hasattr(app.state, 'message_router'):
            await app.state.message_router.shutdown()
        
        # Cleanup health monitoring
        if hasattr(app.state, 'health_orchestrator'):
            await app.state.health_orchestrator.shutdown()
            
        logger.info("Services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Error during service cleanup: {e}")


# Create FastAPI application
app = FastAPI(
    title="TaxPoynt Platform API",
    description="Enterprise Nigerian e-invoicing and business integration platform",
    version="1.0.0",
    debug=DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if DEBUG else [
        "api.taxpoynt.com",
        "api-staging.taxpoynt.com",
        "localhost"
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else [
        "https://app.taxpoynt.com",
        "https://app-staging.taxpoynt.com",
        "http://localhost:3000"  # Local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "service": "taxpoynt_platform_backend",
        "environment": ENVIRONMENT,
        "timestamp": "2024-12-31T00:00:00Z"
    })


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "message": "TaxPoynt Platform Backend API",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "documentation": "/docs" if DEBUG else "Contact admin for API documentation",
        "api_prefix": "/api"
    })


# Setup API Gateway when services are initialized
@app.on_event("startup")
async def setup_api_gateway():
    """Setup API Gateway with all middleware and routing"""
    try:
        # Wait for core services to be initialized
        await asyncio.sleep(0.1)  # Small delay to ensure lifespan startup completes
        
        # Create gateway components
        role_detector = HTTPRoleDetector()
        permission_guard = APIPermissionGuard()
        version_coordinator = APIVersionCoordinator()
        
        # Create main gateway router
        gateway_router = create_main_gateway_router(
            role_detector=role_detector,
            permission_guard=permission_guard,
            message_router=app.state.message_router,
            version_coordinator=version_coordinator
        )
        
        # Create and apply middleware stack
        middleware_stack = create_middleware_stack(
            role_detector=role_detector,
            permission_guard=permission_guard,
            version_coordinator=version_coordinator
        )
        
        # Apply middleware to app
        for middleware_class, middleware_args in middleware_stack:
            app.add_middleware(middleware_class, **middleware_args)
        
        # Include the gateway router
        app.include_router(gateway_router)
        
        logger.info("🌐 API Gateway configured successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup API Gateway: {e}")
        raise


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", "unknown")
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting TaxPoynt Platform Backend on {API_HOST}:{API_PORT}")
    
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG,
        log_level="info" if not DEBUG else "debug"
    )