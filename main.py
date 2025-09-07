#!/usr/bin/env python3
"""
TaxPoynt Platform - Root Entry Point
====================================

This file serves as the entry point for Railway deployment.
It properly imports and runs the backend application from the platform/backend directory.

The actual application logic is in platform/backend/main.py
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = f"{project_root}/platform/backend:{project_root}"

# Import and run the actual backend application
try:
    # Add the backend directory to path and import directly
    backend_dir = project_root / "platform" / "backend"
    sys.path.insert(0, str(backend_dir))
    
    print(f"🔍 Backend directory: {backend_dir}")
    print(f"🔍 Python path: {sys.path[:3]}")
    
    # Import the backend main module
    print("📦 Importing backend main module...")
    import main as backend_main
    print("✅ Backend main module imported successfully")
    
    app = backend_main.app
    print("✅ Backend app accessed successfully")
    
    if __name__ == "__main__":
        import uvicorn
        
        # Get configuration from environment variables
        host = os.getenv("UVICORN_HOST", "0.0.0.0")
        port = int(os.getenv("UVICORN_PORT", "8000"))
        workers = int(os.getenv("UVICORN_WORKERS", "1"))
        log_level = os.getenv("UVICORN_LOG_LEVEL", "info")
        
        # Run the application
        uvicorn.run(
            app,
            host=host,
            port=port,
            workers=workers if workers > 1 else None,  # Only use workers if > 1
            log_level=log_level,
            access_log=True,
            reload=False  # Disable reload in production
        )
        
except ImportError as e:
    print(f"❌ Failed to import backend application: {e}")
    print(f"🔍 Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    print(f"🔍 sys.path: {sys.path}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to start application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)