"""
TaxPoynt Platform Backend - Main Application Entry Point
========================================================
Minimal FastAPI application for Railway deployment
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = ENVIRONMENT == "development"

# Create FastAPI application
app = FastAPI(
    title="TaxPoynt Platform API",
    description="Enterprise Nigerian e-invoicing and business integration platform", 
    version="1.0.0",
    debug=DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Railway health check endpoint"""
    return {
        "status": "healthy",
        "service": "taxpoynt_platform_backend",
        "environment": ENVIRONMENT
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "TaxPoynt Platform Backend API",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "status": "operational"
    }

@app.get("/api/health")
async def api_health():
    """API health check"""
    return {
        "status": "healthy",
        "api_version": "v1",
        "service": "api_gateway"
    }

# Startup event
@app.on_event("startup")
async def startup():
    logger.info("🚀 TaxPoynt Platform Backend starting up...")
    logger.info("✅ Basic FastAPI app ready!")

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