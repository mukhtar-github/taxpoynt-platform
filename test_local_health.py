#!/usr/bin/env python3
"""
Local Health Check Test
=======================
Quick test to validate the health endpoint works before Railway deployment
"""

import sys
import os
import requests
import time
import subprocess
from pathlib import Path

# Add platform backend to path
backend_path = Path(__file__).parent / "platform" / "backend"
sys.path.append(str(backend_path))

def test_health_endpoint_locally():
    """Test the health endpoint by running the server locally"""
    print("🚀 Testing TaxPoynt Platform Health Endpoint Locally")
    print("=" * 50)
    
    # Change to backend directory
    os.chdir(backend_path)
    
    # Start server in background
    print("⏳ Starting FastAPI server...")
    server_process = None
    
    try:
        # Start uvicorn server
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--log-level", "info"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("⌛ Waiting for server startup...")
        time.sleep(3)
        
        # Test health endpoint
        print("🔍 Testing health endpoint...")
        
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=5)
            
            if response.status_code == 200:
                print("✅ Health endpoint SUCCESS!")
                print(f"📊 Status Code: {response.status_code}")
                print(f"📄 Response: {response.json()}")
                
                # Test root endpoint too
                root_response = requests.get("http://127.0.0.1:8000/", timeout=5)
                if root_response.status_code == 200:
                    print("✅ Root endpoint SUCCESS!")
                    print(f"📄 Root Response: {root_response.json()}")
                else:
                    print(f"⚠️  Root endpoint returned {root_response.status_code}")
                    
                return True
            else:
                print(f"❌ Health endpoint failed with status {response.status_code}")
                print(f"📄 Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False
        
    finally:
        # Clean up server process
        if server_process:
            print("🛑 Stopping server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking Dependencies")
    print("-" * 30)
    
    required_packages = ["fastapi", "uvicorn", "starlette", "pydantic"]
    all_available = True
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: Available")
        except ImportError:
            print(f"❌ {package}: Missing")
            all_available = False
    
    return all_available

def main():
    """Main test function"""
    print("🧪 TAXPOYNT PLATFORM - LOCAL HEALTH CHECK TEST")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Missing required dependencies!")
        print("💡 Run: pip install fastapi uvicorn starlette pydantic")
        return False
    
    print("\n🔧 Dependencies OK - Testing Health Endpoint")
    
    # Test health endpoint
    success = test_health_endpoint_locally()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 LOCAL TEST: SUCCESS")
        print("✅ Health endpoint is working correctly")
        print("🚀 Ready for Railway deployment!")
    else:
        print("❌ LOCAL TEST: FAILED") 
        print("🔧 Fix the issues before deploying to Railway")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)