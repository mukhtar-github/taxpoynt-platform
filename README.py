# TaxPoynt Platform - Python FastAPI Application
# This file ensures Railway detects this as a Python project

"""
TaxPoynt eInvoice Platform - Production Deployment

This is a Python FastAPI application for Nigerian e-invoicing and FIRS integration.

Entry Point: main.py
Framework: FastAPI + Uvicorn
Database: PostgreSQL
Cache: Redis
Deployment: Railway Cloud

Health Check: /health
API Documentation: /docs (disabled in production)
"""

# Application metadata
APP_NAME = "TaxPoynt Platform"
APP_VERSION = "2.0.0"
PYTHON_VERSION = "3.11.9"
FRAMEWORK = "FastAPI"

if __name__ == "__main__":
    print(f"{APP_NAME} v{APP_VERSION}")
    print(f"Python {PYTHON_VERSION} + {FRAMEWORK}")
    print("Run: python main.py")