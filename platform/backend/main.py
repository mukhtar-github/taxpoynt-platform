"""
TaxPoynt E-Invoice Platform Backend
==================================
Main application entry point with API Gateway architecture integration.
"""
import os
import sys
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
        
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            # Immediate health response for Railway
            return JSONResponse({
                "status": "healthy",
                "service": "taxpoynt_platform_backend",
                "environment": ENVIRONMENT,
                "railway_deployment": RAILWAY_DEPLOYMENT,
                "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
                "timestamp": datetime.now().isoformat()
            })
        
        return await call_next(request)

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
    
    # Core platform components with fallback handling
    try:
        from core_platform.authentication.role_manager import RoleManager
        from core_platform.messaging.message_router import MessageRouter, ServiceRole
    except ImportError:
        # Use fallback classes from gateway
        from api_gateway.role_routing.gateway import RoleManager
        from api_gateway.role_routing import MessageRouter, ServiceRole
    
    GATEWAY_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("✅ Successfully imported TaxPoynt API Gateway components")
    
except ImportError as e:
    logger.error(f"❌ Gateway components not available: {e}")
    GATEWAY_AVAILABLE = False

def create_role_manager():
    """Create and initialize role manager"""
    if not GATEWAY_AVAILABLE:
        return None
        
    config = {
        'service_name': 'TaxPoynt_RoleManager',
        'environment': ENVIRONMENT,
        'log_level': 'INFO' if not DEBUG else 'DEBUG'
    }
    return RoleManager(config) if GATEWAY_AVAILABLE else None

def create_message_router():
    """Create and initialize message router"""  
    if not GATEWAY_AVAILABLE:
        return None
    
    # This will be properly initialized with your existing message router
    # For now, we create a basic instance that works with your architecture
    return MessageRouter() if GATEWAY_AVAILABLE else None

def create_taxpoynt_app() -> FastAPI:
    """Create TaxPoynt application with proper architecture integration"""
    
    if GATEWAY_AVAILABLE:
        # Use sophisticated API gateway architecture
        logger.info("🚀 Initializing TaxPoynt Platform with API Gateway")
        
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
        
        config = APIGatewayConfig(
            host="0.0.0.0",
            port=PORT,
            cors_enabled=True,
            cors_origins=allowed_origins,
            trusted_hosts=["taxpoynt.com", "*.taxpoynt.com"] if not DEBUG else None,
            security=RoutingSecurityLevel.STANDARD,
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "taxpoynt-platform-secret-key"),
            jwt_expiration_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440")),
            enable_request_logging=True,
            enable_metrics=True,
            log_level="INFO" if not DEBUG else "DEBUG"
        )
        
        # Create core platform components
        role_manager = create_role_manager()
        message_router = create_message_router()
        
        # Create API gateway
        gateway = TaxPoyntAPIGateway(config, role_manager, message_router)
        app = gateway.get_app()
        
        # Add health check middleware
        app.add_middleware(HealthCheckMiddleware)
        
        logger.info("✅ TaxPoynt Platform initialized with full API Gateway")
        return app
        
    else:
        # Fallback mode - basic FastAPI app
        logger.info("🔄 Initializing TaxPoynt Platform in basic mode")
        
        app = FastAPI(
            title="TaxPoynt Platform API",
            description="Enterprise Nigerian e-invoicing and business integration platform", 
            version="1.0.0",
            debug=DEBUG,
            docs_url="/docs" if DEBUG else None,
            redoc_url="/redoc" if DEBUG else None,
        )
        
        # Add health check middleware FIRST
        app.add_middleware(HealthCheckMiddleware)
        
        # Add CORS middleware
        allowed_origins = [
            "https://web-production-ea5ad.up.railway.app",
            "https://app-staging.taxpoynt.com", 
            "https://app.taxpoynt.com",
            "https://taxpoynt.com",  # Main Vercel domain
            "https://www.taxpoynt.com",  # WWW subdomain
            "http://localhost:3000",
            "http://localhost:3001"  # Frontend dev port
        ] if not DEBUG else ["*"]
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
        
        # Add basic endpoints
        @app.get("/")
        async def api_root():
            return JSONResponse(content={
                "service": "TaxPoynt E-Invoice Platform API",
                "version": "1.0.0", 
                "status": "operational",
                "mode": "basic_fallback",
                "environment": ENVIRONMENT,
                "railway_deployment": RAILWAY_DEPLOYMENT,
                "endpoints": {
                    "health": "/health",
                    "api_health": "/api/health",
                    "docs": "/docs" if DEBUG else "disabled"
                }
            })
        
        # Authentication endpoints are now handled by the API Gateway
        logger.info("✅ Using API Gateway for all authentication and service endpoints")
        
        logger.info("⚠️  TaxPoynt Platform initialized in basic mode")
        return app

# Create the app instance
app = create_taxpoynt_app()

async def initialize_services():
    """Initialize core platform services"""
    if GATEWAY_AVAILABLE:
        try:
            # Initialize role manager
            if hasattr(app.state, 'role_manager') and app.state.role_manager:
                await app.state.role_manager.initialize()
                logger.info("✅ Role Manager initialized")
            
            logger.info("🎯 Core platform services initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize services: {e}")
            raise

async def cleanup_services():
    """Cleanup core platform services"""
    if GATEWAY_AVAILABLE:
        try:
            # Cleanup role manager
            if hasattr(app.state, 'role_manager') and app.state.role_manager:
                await app.state.role_manager.cleanup()
                logger.info("✅ Role Manager cleaned up")
            
            logger.info("🎯 Core platform services cleaned up successfully") 
        except Exception as e:
            logger.error(f"❌ Failed to cleanup services: {e}")

# Add startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("🚀 TaxPoynt Platform Backend starting up...")
    logger.info(f"📊 Environment: {ENVIRONMENT}")
    logger.info(f"🚂 Railway Deployment: {RAILWAY_DEPLOYMENT}")
    logger.info(f"🌐 Port: {PORT}")
    
    if GATEWAY_AVAILABLE:
        logger.info("✅ API Gateway mode: ENABLED")
        logger.info("🔐 Authentication endpoints: /api/v1/auth/*")
        await initialize_services()
    else:
        logger.info("⚠️  API Gateway mode: DISABLED (fallback mode)")
        logger.info("📝 Note: Install gateway dependencies for full functionality")
    
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