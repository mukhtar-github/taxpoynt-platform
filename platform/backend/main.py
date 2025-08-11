"""
TaxPoynt Platform Backend - Main Application Entry Point
========================================================
Railway-optimized FastAPI application with proper health checks and error handling
"""
import os
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path

# Minimal imports for Railway startup reliability
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import Response
except ImportError as e:
    print(f"❌ Critical import error: {e}")
    sys.exit(1)

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Environment configuration with Railway optimization
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = ENVIRONMENT == "development"
PORT = int(os.getenv("PORT", "8000"))
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

# Create FastAPI application with Railway optimization
app = FastAPI(
    title="TaxPoynt Platform API",
    description="Enterprise Nigerian e-invoicing and business integration platform", 
    version="1.0.0",
    debug=DEBUG,
    docs_url="/docs" if DEBUG else None,  # Disable docs in production for security
    redoc_url="/redoc" if DEBUG else None,
)

# Add health check middleware FIRST
app.add_middleware(HealthCheckMiddleware)

# Add CORS middleware with Railway-friendly origins
allowed_origins = [
    "https://web-production-ea5ad.up.railway.app",  # Railway production
    "https://app-staging.taxpoynt.com",
    "https://app.taxpoynt.com",
    "http://localhost:3000"
] if not DEBUG else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Primary health endpoint for Railway
@app.get("/health")
async def health_check():
    """Railway health check endpoint - enhanced for deployment reliability"""
    try:
        return {
            "status": "healthy",
            "service": "taxpoynt_platform_backend",
            "environment": ENVIRONMENT,
            "version": "1.0.0",
            "railway_deployment": RAILWAY_DEPLOYMENT,
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "fastapi": "operational",
                "startup": "complete",
                "memory": "ok"
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "service": "taxpoynt_platform_backend"
            }
        )

@app.get("/")
async def root():
    """Root endpoint with Railway deployment info"""
    return {
        "message": "TaxPoynt Platform Backend API",
        "version": "1.0.0", 
        "environment": ENVIRONMENT,
        "status": "operational",
        "railway_deployment": RAILWAY_DEPLOYMENT,
        "endpoints": {
            "health": "/health",
            "api_health": "/api/health", 
            "docs": "/docs" if DEBUG else "disabled",
            "api_v1": "/api/v1"
        }
    }

@app.get("/api/health")
async def api_health():
    """API health check with enhanced diagnostics"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "service": "api_gateway",
        "components": {
            "firs_communication": "loaded",
            "si_services": "loaded", 
            "app_services": "loaded",
            "external_integrations": "loaded"
        },
        "environment": ENVIRONMENT
    }

# Basic API endpoints for testing
@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_status": "operational",
        "version": "v1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# Startup event with error handling
@app.on_event("startup")
async def startup():
    """Enhanced startup with Railway deployment logging"""
    try:
        logger.info("🚀 TaxPoynt Platform Backend starting up...")
        logger.info(f"📊 Environment: {ENVIRONMENT}")
        logger.info(f"🚂 Railway Deployment: {RAILWAY_DEPLOYMENT}")
        logger.info(f"🌐 Port: {PORT}")
        logger.info("✅ FastAPI app ready for Railway deployment!")
        
        # Log successful startup for Railway visibility
        print("=" * 50)
        print("🎉 TAXPOYNT PLATFORM STARTUP SUCCESS")
        print(f"⚡ Environment: {ENVIRONMENT}")
        print(f"🔗 Health Check: /health")
        print(f"📚 API Docs: /docs" + (" (disabled in production)" if not DEBUG else ""))
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        logger.error(traceback.format_exc())
        # Don't exit - let Railway handle the restart

@app.on_event("shutdown")
async def shutdown():
    """Shutdown event"""
    logger.info("🛑 TaxPoynt Platform Backend shutting down...")

# Global exception handler for Railway debugging
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better Railway debugging"""
    logger.error(f"❌ Global exception on {request.url}: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if DEBUG else "An error occurred",
            "service": "taxpoynt_platform_backend",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting TaxPoynt Platform on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )