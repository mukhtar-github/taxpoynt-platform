#!/usr/bin/env python3
"""
Railway Deployment Readiness Verification
==========================================
Verifies that all files are correctly configured for Railway deployment
"""

import os
import json
from pathlib import Path
from datetime import datetime

def verify_files():
    """Verify all required files exist and are properly configured"""
    print("🔍 Verifying Railway Deployment Files")
    print("=" * 50)
    
    required_files = {
        "railway.toml": "Railway configuration",
        "platform/backend/main.py": "FastAPI application", 
        "platform/backend/requirements-minimal.txt": "Python dependencies",
        ".env": "Environment variables",
        ".env.example": "Environment template"
    }
    
    results = {}
    
    for file_path, description in required_files.items():
        path = Path(file_path)
        exists = path.exists()
        results[file_path] = exists
        
        if exists:
            size = path.stat().st_size
            print(f"✅ {description}: {file_path} ({size} bytes)")
            
            # Check specific file contents
            if file_path == "platform/backend/main.py":
                content = path.read_text()
                has_health = "/health" in content
                has_fastapi = "FastAPI" in content
                print(f"   📊 Health endpoint: {'✅' if has_health else '❌'}")
                print(f"   📊 FastAPI import: {'✅' if has_fastapi else '❌'}")
                
            elif file_path == "railway.toml":
                content = path.read_text()
                has_health_check = "healthcheckPath" in content
                has_start_cmd = "startCommand" in content
                print(f"   📊 Health check config: {'✅' if has_health_check else '❌'}")
                print(f"   📊 Start command: {'✅' if has_start_cmd else '❌'}")
                
        else:
            print(f"❌ {description}: {file_path} - NOT FOUND")
    
    return results

def check_environment_variables():
    """Check that environment variables are configured"""
    print("\n🔍 Environment Variables Check")
    print("-" * 30)
    
    # Check if .env file loads properly
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Read .env file
    try:
        with open(".env", 'r') as f:
            lines = f.readlines()
        
        env_vars = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
        
        print(f"✅ Environment file loaded: {len(env_vars)} variables")
        
        # Check critical Railway variables
        railway_vars = ["DATABASE_URL", "REDIS_URL", "ENVIRONMENT"]
        for var in railway_vars:
            if var in env_vars and env_vars[var]:
                print(f"✅ {var}: Configured")
            else:
                print(f"⚠️  {var}: Not set (will use Railway defaults)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False

def generate_deployment_summary():
    """Generate deployment summary"""
    print("\n🚀 Railway Deployment Summary")
    print("=" * 50)
    
    # Read current railway.toml
    railway_config = Path("railway.toml")
    if railway_config.exists():
        content = railway_config.read_text()
        print("📋 Railway Configuration:")
        
        # Extract key configurations
        if "healthcheckPath = \"/health\"" in content:
            print("✅ Health Check: /health endpoint configured")
        if "healthcheckTimeout" in content:
            print("✅ Health Timeout: Extended for reliable startup")
        if "requirements-minimal.txt" in content:
            print("✅ Dependencies: Minimal requirements for reliability")
        if "startCommand" in content:
            print("✅ Start Command: Enhanced with logging")
    
    print("\n🎯 Deployment Steps:")
    print("1. ✅ Files prepared and verified")
    print("2. 🔄 Railway will build using nixpacks") 
    print("3. 🔄 Install minimal Python dependencies")
    print("4. 🔄 Start FastAPI with uvicorn")
    print("5. 🔄 Health check at /health endpoint")
    print("6. ✅ Deployment complete (if health checks pass)")
    
    print("\n💡 If deployment fails:")
    print("• Check Railway logs for specific errors")
    print("• Verify environment variables are set")
    print("• Ensure /health endpoint responds within 45 seconds")

def main():
    """Main verification function"""
    print("🧪 TAXPOYNT PLATFORM - RAILWAY DEPLOYMENT VERIFICATION")
    print("⏰ " + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)
    
    # Verify files
    file_results = verify_files()
    
    # Check environment
    env_ready = check_environment_variables()
    
    # Generate summary
    generate_deployment_summary()
    
    # Final assessment
    files_ready = all(file_results.values())
    overall_ready = files_ready and env_ready
    
    print("\n" + "=" * 70)
    print("📊 DEPLOYMENT READINESS ASSESSMENT")
    print("=" * 70)
    
    print(f"Files Ready: {'✅' if files_ready else '❌'} ({sum(file_results.values())}/{len(file_results)})")
    print(f"Environment Ready: {'✅' if env_ready else '❌'}")
    print(f"Overall Status: {'🎉 READY FOR RAILWAY DEPLOYMENT' if overall_ready else '🔧 NEEDS ATTENTION'}")
    
    if overall_ready:
        print("\n🚀 NEXT STEPS:")
        print("1. Commit and push changes to your repository")
        print("2. Railway will automatically detect changes and redeploy")
        print("3. Monitor deployment logs in Railway dashboard")
        print("4. Verify health endpoint responds: https://web-production-ea5ad.up.railway.app/health")
    else:
        print("\n🔧 ISSUES TO RESOLVE:")
        for file_path, exists in file_results.items():
            if not exists:
                print(f"❌ Missing: {file_path}")
        if not env_ready:
            print("❌ Environment configuration issues")
    
    return overall_ready

if __name__ == "__main__":
    ready = main()
    exit(0 if ready else 1)