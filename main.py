# TaxPoynt Platform - Root Entry Point
# This file helps Railway detect this as a Python project

import sys
import os
from pathlib import Path

# Add platform backend to Python path
backend_path = Path(__file__).parent / "platform" / "backend"
sys.path.insert(0, str(backend_path))

# Import and run the main FastAPI application
try:
    os.chdir(backend_path)
    from main import app
    
    if __name__ == "__main__":
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    
except ImportError as e:
    print(f"Error importing FastAPI app: {e}")
    sys.exit(1)