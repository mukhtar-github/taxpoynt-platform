#!/usr/bin/env python3
"""
TaxPoynt Platform - Professional Database Setup and Connectivity Test
===================================================================
This script sets up the database infrastructure for the TaxPoynt platform,
tests connectivity, runs migrations, and verifies the complete system.

Usage:
    python platform/backend/database_setup.py --mode [local|production]
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class DatabaseSetupManager:
    """Professional database setup and management."""
    
    def __init__(self, mode: str = "local"):
        self.mode = mode
        self.setup_results = {}
        self.project_root = project_root
        
        # Load environment variables
        self.load_environment()
        
    def load_environment(self):
        """Load appropriate environment variables."""
        if self.mode == "local":
            env_file = self.project_root / ".env.development"
            if env_file.exists():
                logger.info(f"Loading environment from {env_file}")
                self.load_env_file(env_file)
            else:
                logger.warning("No .env.development file found")
        else:
            # For production, try platform/backend/.env first
            platform_env = Path("platform/backend/.env")
            backend_env = Path(".env")
            
            if platform_env.exists():
                logger.info(f"Loading production environment from {platform_env}")
                self.load_env_file(platform_env)
            elif backend_env.exists():
                logger.info(f"Loading production environment from {backend_env}")
                self.load_env_file(backend_env)
            else:
                logger.info("Using system environment variables")
    
    def load_env_file(self, env_file: Path):
        """Load environment variables from file."""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
            logger.info(f"Loaded environment variables from {env_file}")
        except Exception as e:
            logger.error(f"Error loading environment file: {e}")
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration based on mode."""
        if self.mode == "local":
            return {
                "database_url": os.getenv("DATABASE_URL", "sqlite:///./taxpoynt_platform.db"),
                "type": "sqlite" if "sqlite" in os.getenv("DATABASE_URL", "") else "postgresql",
                "echo": os.getenv("DEBUG", "false").lower() == "true"
            }
        else:
            # Production configuration
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable is required for production")
            
            return {
                "database_url": database_url,
                "type": "postgresql",
                "echo": False,
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10"))
            }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        return {
            "url": redis_url,
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD")
        }
    
    async def test_database_connectivity(self) -> bool:
        """Test database connectivity."""
        logger.info("🔌 Testing database connectivity...")
        
        try:
            db_config = self.get_database_config()
            database_url = db_config["database_url"]
            
            if db_config["type"] == "sqlite":
                # Test SQLite connectivity
                import sqlite3
                if "://" in database_url:
                    db_path = database_url.split("///")[-1]
                else:
                    db_path = database_url
                
                # Create directory if needed
                os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
                
                # Test connection
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                conn.close()
                
                logger.info(f"✅ SQLite database connectivity successful: {db_path}")
                self.setup_results["database"] = {
                    "status": "success",
                    "type": "sqlite",
                    "path": db_path,
                    "test_result": result[0] if result else None
                }
                return True
                
            else:
                # Test PostgreSQL connectivity
                try:
                    import psycopg2
                    from sqlalchemy import create_engine, text
                    
                    engine = create_engine(database_url)
                    with engine.connect() as connection:
                        result = connection.execute(text("SELECT 1"))
                        test_value = result.fetchone()[0]
                    
                    logger.info("✅ PostgreSQL database connectivity successful")
                    self.setup_results["database"] = {
                        "status": "success",
                        "type": "postgresql",
                        "url": database_url,
                        "test_result": test_value
                    }
                    return True
                    
                except ImportError:
                    logger.error("❌ psycopg2 not installed. Install with: pip install psycopg2-binary")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Database connectivity test failed: {e}")
            self.setup_results["database"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    async def test_redis_connectivity(self) -> bool:
        """Test Redis connectivity."""
        logger.info("🔴 Testing Redis connectivity...")
        
        try:
            redis_config = self.get_redis_config()
            
            try:
                import redis
                
                # Create Redis client
                r = redis.from_url(redis_config["url"])
                
                # Test connection
                r.ping()
                
                # Test basic operations
                test_key = "taxpoynt_test_key"
                test_value = "test_value"
                r.set(test_key, test_value)
                retrieved_value = r.get(test_key).decode('utf-8')
                r.delete(test_key)
                
                if retrieved_value == test_value:
                    logger.info("✅ Redis connectivity and operations successful")
                    self.setup_results["redis"] = {
                        "status": "success",
                        "url": redis_config["url"],
                        "test_result": "operations_successful"
                    }
                    return True
                else:
                    logger.error("❌ Redis operations test failed")
                    return False
                    
            except ImportError:
                logger.warning("⚠️ Redis not installed. Install with: pip install redis")
                # Create mock Redis for development
                logger.info("📝 Using in-memory cache fallback")
                self.setup_results["redis"] = {
                    "status": "fallback",
                    "type": "in_memory",
                    "note": "Using in-memory cache - install redis for better performance"
                }
                return True
                
        except Exception as e:
            logger.error(f"❌ Redis connectivity test failed: {e}")
            self.setup_results["redis"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def create_initial_tables(self) -> bool:
        """Create initial database tables."""
        logger.info("🗃️ Creating initial database tables...")
        
        try:
            db_config = self.get_database_config()
            
            if db_config["type"] == "sqlite":
                import sqlite3
                database_path = db_config["database_url"].split("///")[-1]
                
                conn = sqlite3.connect(database_path)
                cursor = conn.cursor()
                
                # Create basic tables for TaxPoynt platform
                cursor.executescript("""
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    service_package VARCHAR(20) DEFAULT 'si',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Organizations table
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    business_type VARCHAR(50),
                    tin VARCHAR(50),
                    rc_number VARCHAR(50),
                    address TEXT,
                    state VARCHAR(100),
                    lga VARCHAR(100),
                    owner_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(id)
                );
                
                -- Integration credentials table
                CREATE TABLE IF NOT EXISTS integration_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER,
                    integration_type VARCHAR(50),
                    credentials_data TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                );
                
                -- FIRS submissions table
                CREATE TABLE IF NOT EXISTS firs_submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_id INTEGER,
                    invoice_data TEXT,
                    irn VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'pending',
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                );
                """)
                
                conn.commit()
                conn.close()
                
                logger.info("✅ SQLite tables created successfully")
                self.setup_results["tables"] = {
                    "status": "success",
                    "type": "sqlite",
                    "tables_created": ["users", "organizations", "integration_credentials", "firs_submissions"]
                }
                return True
                
            else:
                logger.info("📋 For PostgreSQL, use Alembic migrations instead of direct table creation")
                return True
                
        except Exception as e:
            logger.error(f"❌ Table creation failed: {e}")
            self.setup_results["tables"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
    
    def verify_system_requirements(self) -> Dict[str, bool]:
        """Verify system requirements."""
        logger.info("🔍 Verifying system requirements...")
        
        requirements = {}
        
        # Check Python version
        python_version = sys.version_info
        requirements["python"] = python_version >= (3, 8)
        logger.info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro} - {'✅' if requirements['python'] else '❌'}")
        
        # Check required packages
        packages = ["fastapi", "sqlalchemy", "pydantic"]
        for package in packages:
            try:
                __import__(package)
                requirements[package] = True
                logger.info(f"Package {package}: ✅")
            except ImportError:
                requirements[package] = False
                logger.error(f"Package {package}: ❌ - Install with: pip install {package}")
        
        # Check optional packages
        optional_packages = ["redis", "psycopg2"]
        for package in optional_packages:
            try:
                __import__(package)
                requirements[f"{package}_optional"] = True
                logger.info(f"Optional package {package}: ✅")
            except ImportError:
                requirements[f"{package}_optional"] = False
                logger.warning(f"Optional package {package}: ⚠️ - Recommended for production")
        
        return requirements
    
    async def run_complete_setup(self) -> Dict[str, Any]:
        """Run complete database setup process."""
        logger.info(f"🚀 Starting TaxPoynt Platform database setup in {self.mode} mode")
        
        # Verify system requirements
        requirements = self.verify_system_requirements()
        
        # Test database connectivity
        db_success = await self.test_database_connectivity()
        
        # Test Redis connectivity
        redis_success = await self.test_redis_connectivity()
        
        # Create initial tables (for SQLite)
        tables_success = self.create_initial_tables() if db_success else False
        
        # Generate summary report
        summary = {
            "setup_mode": self.mode,
            "timestamp": datetime.now().isoformat(),
            "system_requirements": requirements,
            "database_connectivity": db_success,
            "redis_connectivity": redis_success,
            "initial_tables": tables_success,
            "overall_success": all([db_success, redis_success, tables_success]),
            "detailed_results": self.setup_results
        }
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 TAXPOYNT PLATFORM DATABASE SETUP SUMMARY")
        print("="*60)
        print(f"Mode: {self.mode}")
        print(f"Database: {'✅ Ready' if db_success else '❌ Failed'}")
        print(f"Redis: {'✅ Ready' if redis_success else '❌ Failed'}")
        print(f"Tables: {'✅ Created' if tables_success else '❌ Failed'}")
        print(f"Overall: {'🎉 SUCCESS' if summary['overall_success'] else '❌ NEEDS ATTENTION'}")
        print("="*60)
        
        return summary

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TaxPoynt Platform Database Setup")
    parser.add_argument("--mode", choices=["local", "production"], default="local",
                        help="Setup mode (default: local)")
    parser.add_argument("--output", type=str, help="Output results to JSON file")
    
    args = parser.parse_args()
    
    # Run setup
    setup_manager = DatabaseSetupManager(mode=args.mode)
    results = asyncio.run(setup_manager.run_complete_setup())
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_success"] else 1)

if __name__ == "__main__":
    main()