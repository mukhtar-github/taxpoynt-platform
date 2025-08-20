#!/usr/bin/env python3
"""
Debug startup script to help identify Railway deployment issues
"""

import sys
import os
import traceback
from pathlib import Path

print("=== TaxPoynt Platform Debug Startup ===")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    print("Step 1: Setting up paths...")
    backend_path = Path(__file__).parent / "platform" / "backend"
    print(f"Backend path: {backend_path}")
    print(f"Backend path exists: {backend_path.exists()}")
    
    if backend_path.exists():
        print("Step 2: Adding backend to Python path...")
        sys.path.insert(0, str(backend_path))
        
        print("Step 3: Changing working directory...")
        os.chdir(backend_path)
        print(f"New working directory: {os.getcwd()}")
        
        print("Step 4: Attempting to import main app...")
        from main import app
        print("✅ Successfully imported FastAPI app!")
        
        print("Step 5: Starting uvicorn server...")
        import uvicorn
        port = int(os.environ.get("PORT", 8000))
        print(f"Starting server on port {port}")
        
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
        
    else:
        print("❌ Backend path does not exist!")
        print("Available directories:")
        for item in Path(__file__).parent.iterdir():
            if item.is_dir():
                print(f"  - {item.name}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("Full traceback:")
    traceback.print_exc()
    sys.exit(1)