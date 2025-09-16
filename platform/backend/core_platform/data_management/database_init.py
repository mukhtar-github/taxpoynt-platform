"""
TaxPoynt Platform - Database Initialization
==========================================

Comprehensive database initialization for the TaxPoynt platform.
Handles database connection, table creation, and initial data setup.
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from alembic import command
from alembic.config import Config
import warnings
from pathlib import Path

from .models import (
    Base, User, UserRole, UserServiceAccess, Organization, OrganizationUser,
    Integration, IntegrationCredentials, FIRSSubmission,
    BankingConnection, BankAccount, BankTransaction, BankingWebhook,
    BankingSyncLog, BankingCredentials, BankingProvider
)
from ..config.environment import get_config

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """
    Database initialization and management for TaxPoynt platform.
    
    Handles:
    - Database connection setup
    - Table creation and migrations
    - Initial data seeding
    - Banking model initialization
    - Environment-specific configurations
    """
    
    def __init__(self):
        self.config = get_config()
        self.database_config = self.config.get_database_config()
        self.database_url = self.database_config["url"]
        self.environment = self.config.environment.value
        self.engine = None
        self.SessionLocal = None
        self.is_initialized = False
        
        # Database configuration from environment config
        self.engine_kwargs = {
            "pool_size": self.database_config["pool_size"],
            "max_overflow": self.database_config["max_overflow"],
            "echo": self.database_config["echo"],
            "pool_pre_ping": self.database_config["pool_pre_ping"],
            "pool_recycle": 300,
        }
        
        # Validate database URL exists
        if not self.database_url:
            error_msg = f"No database URL configured for {self.environment} environment"
            logger.error(error_msg)
            if self.environment == "development":
                logger.info("💡 To set up local development database, run: docker-compose -f docker-compose.dev.yml up -d")
            raise ValueError(error_msg)
    
    async def initialize_database(self) -> Dict[str, Any]:
        """
        Complete database initialization.
        
        Returns:
            Initialization status and details
        """
        try:
            logger.info("🗄️  Starting database initialization...")
            logger.info(f"📊 Environment: {self.environment}")
            logger.info(f"🔗 Database: {'PostgreSQL' if 'postgresql' in self.database_url else 'SQLite'}")
            
            # Step 1: Create database engine
            await self._create_engine()
            
            # Step 2: Create all tables
            await self._create_tables()
            
            # Step 3: Seed initial data
            await self._seed_initial_data()
            
            # Step 4: Initialize banking-specific data
            await self._initialize_banking_data()
            
            self.is_initialized = True
            
            logger.info("✅ Database initialization completed successfully!")
            
            return {
                "status": "initialized",
                "database_type": "PostgreSQL" if "postgresql" in self.database_url else "SQLite",
                "environment": self.environment,
                "tables_created": len(Base.metadata.tables),
                "banking_models": [
                    "BankingConnection", "BankAccount", "BankTransaction",
                    "BankingWebhook", "BankingSyncLog", "BankingCredentials"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            raise RuntimeError(f"Database initialization failed: {str(e)}")
    
    async def _create_engine(self):
        """Create database engine and session factory"""
        try:
            self.engine = create_engine(self.database_url, **self.engine_kwargs)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Test connection
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            
            logger.info("✅ Database engine created and connection tested")
            
        except Exception as e:
            logger.error(f"❌ Failed to create database engine: {e}")
            raise
    
    async def _create_tables(self):
        """Initialize database schema (migrations or dev create_all)."""
        try:
            is_postgres = "postgresql" in (self.database_url or "").lower() or "postgres://" in (self.database_url or "").lower()
            enable_alembic = os.getenv("ALEMBIC_RUN_ON_STARTUP", "true").lower() == "true"
            allow_create_all = os.getenv("ALLOW_CREATE_ALL", "false").lower() == "true"

            if is_postgres and enable_alembic:
                logger.info("📜 Applying Alembic migrations (PostgreSQL detected)...")
                await self._run_alembic_migrations()
                logger.info("✅ Alembic migrations applied")
            else:
                # Dev-only fallback: create_all for lightweight local setups
                if self.environment in ("development", "dev", "testing", "test") or allow_create_all:
                    logger.info("🛠️ Dev/test environment detected – creating tables via Base.metadata.create_all")
                    Base.metadata.create_all(bind=self.engine)
                    table_count = len(Base.metadata.tables)
                    logger.info(f"✅ Created {table_count} database tables (dev/test)")
                    table_names = list(Base.metadata.tables.keys())
                    logger.info(f"📊 Tables: {', '.join(table_names)}")
                else:
                    logger.info("ℹ️ Skipping create_all in non-dev environment (set ALEMBIC_RUN_ON_STARTUP=true to apply migrations)")

            # Create production indexes for performance (PostgreSQL only)
            if is_postgres:
                await self._create_production_indexes()

        except Exception as e:
            logger.error(f"❌ Failed to initialize schema: {e}")
            raise

    async def _run_alembic_migrations(self) -> None:
        """Run Alembic migrations to head using programmatic API.

        Resolves migration script location from environment or known paths.
        Honors ALEMBIC_FAIL_ON_STARTUP_ERROR (default true) to control failure mode.
        """
        try:
            # Resolve script_location
            script_path_env = os.getenv("ALEMBIC_MIGRATIONS_PATH")
            base_dir = Path(__file__).resolve().parents[4]  # points to platform/backend
            candidates = [
                Path(script_path_env) if script_path_env else None,
                base_dir / "alembic",
                base_dir.parent / "archive" / "legacy" / "backend" / "alembic",
            ]
            script_location = None
            for cand in candidates:
                if cand and cand.exists() and (cand / "env.py").exists():
                    script_location = str(cand)
                    break

            if not script_location:
                raise RuntimeError("Could not locate Alembic migrations directory. Set ALEMBIC_MIGRATIONS_PATH.")

            cfg = Config()
            cfg.set_main_option("script_location", script_location)
            cfg.set_main_option("sqlalchemy.url", self.database_url)
            # Optional: quiet logging unless explicitly enabled
            if os.getenv("ALEMBIC_LOG_LEVEL"):
                cfg.set_main_option("log_level", os.getenv("ALEMBIC_LOG_LEVEL", "INFO"))

            # Run upgrade to head
            command.upgrade(cfg, "head")
        except Exception as e:
            fail = os.getenv("ALEMBIC_FAIL_ON_STARTUP_ERROR", "true").lower() == "true"
            logger.error(f"Alembic migration error: {e}")
            if fail:
                raise
            logger.warning("Continuing startup without applying migrations due to configuration")
    
    async def _create_production_indexes(self):
        """Create production database indexes for performance"""
        try:
            logger.info("🔧 Creating production database indexes...")
            
            from .database_indexes import create_production_indexes
            
            with self.SessionLocal() as session:
                index_results = create_production_indexes(session)
                
                total_indexes = sum(len(result) for result in index_results.values() if isinstance(result, list))
                logger.info(f"✅ Created {total_indexes} production indexes for high-volume transactions")
                
        except ImportError:
            logger.warning("⚠️  Database indexes module not available, skipping index creation")
        except Exception as e:
            logger.error(f"❌ Failed to create production indexes: {e}")
            # Don't raise - indexes are important but not critical for basic functionality
    
    async def _seed_initial_data(self):
        """Seed initial data for the platform"""
        try:
            with self.SessionLocal() as session:
                # Check if data already exists
                existing_users = session.query(User).count()
                if existing_users > 0:
                    logger.info("📊 Initial data already exists, skipping seed")
                    return
                
                # Create initial admin user
                admin_user = User(
                    email="admin@taxpoynt.com",
                    username="admin",
                    first_name="TaxPoynt",
                    last_name="Administrator",
                    is_active=True,
                    is_verified=True
                )
                session.add(admin_user)
                
                # Create user roles
                admin_role = UserRole(
                    user=admin_user,
                    role="administrator",
                    scope="global"
                )
                session.add(admin_role)
                
                # Create initial organization
                org = Organization(
                    name="TaxPoynt Platform",
                    description="TaxPoynt E-Invoice Platform Organization",
                    business_type="technology",
                    tax_identification_number="00000000-0000-0000",
                    country="NG",
                    is_active=True
                )
                session.add(org)
                
                session.commit()
                logger.info("✅ Initial data seeded successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to seed initial data: {e}")
            raise
    
    async def _initialize_banking_data(self):
        """Initialize banking-specific data and configurations"""
        try:
            with self.SessionLocal() as session:
                # Check if banking data already exists
                existing_connections = session.query(BankingConnection).count()
                if existing_connections > 0:
                    logger.info("🏦 Banking data already exists, skipping initialization")
                    return
                
                # Create default banking credentials (sandbox)
                if self.environment == "development":
                    from .models.banking import BankingCredentials
                    
                    mono_creds = BankingCredentials(
                        si_id="00000000-0000-0000-0000-000000000000",  # Default SI
                        provider=BankingProvider.MONO,
                        environment="sandbox",
                        api_key=os.getenv("MONO_API_KEY", "test_key"),
                        client_id=os.getenv("MONO_CLIENT_ID", "test_client"),
                        client_secret=os.getenv("MONO_CLIENT_SECRET", "test_secret"),
                        webhook_secret=os.getenv("MONO_WEBHOOK_SECRET", "test_webhook_secret"),
                        is_active=True,
                        validation_status="pending"
                    )
                    session.add(mono_creds)
                    
                    session.commit()
                    logger.info("✅ Banking credentials initialized for development")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize banking data: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        if not self.is_initialized:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        return self.SessionLocal()
    
    def get_engine(self):
        """Get database engine"""
        if not self.is_initialized:
            raise RuntimeError("Database not initialized. Call initialize_database() first.")
        return self.engine
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            if not self.engine:
                return {"status": "unhealthy", "error": "Database not initialized"}
            
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1")).fetchone()
                
                with self.SessionLocal() as session:
                    user_count = session.query(User).count()
                    org_count = session.query(Organization).count()
                    banking_count = session.query(BankingConnection).count()
                
                return {
                    "status": "healthy",
                    "connection": "active",
                    "tables": len(Base.metadata.tables),
                    "data_summary": {
                        "users": user_count,
                        "organizations": org_count,
                        "banking_connections": banking_count
                    }
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup database connections"""
        try:
            if self.engine:
                self.engine.dispose()
                logger.info("✅ Database connections cleaned up")
        except Exception as e:
            logger.error(f"❌ Database cleanup failed: {e}")


# Global database initializer instance
_database_initializer: Optional[DatabaseInitializer] = None


async def initialize_database() -> DatabaseInitializer:
    """
    Initialize the database for TaxPoynt platform.
    
    Returns:
        Initialized database instance
    """
    global _database_initializer
    
    if _database_initializer is None or not _database_initializer.is_initialized:
        _database_initializer = DatabaseInitializer()
        await _database_initializer.initialize_database()
    
    return _database_initializer


def get_database() -> Optional[DatabaseInitializer]:
    """Get the global database initializer instance"""
    return _database_initializer


async def cleanup_database():
    """Cleanup database connections"""
    global _database_initializer
    
    if _database_initializer:
        await _database_initializer.cleanup()
        _database_initializer = None


# Dependency for FastAPI
def get_db_session():
    """FastAPI dependency for database sessions (deprecated for handlers).

    Deprecated: Do not use this as a FastAPI dependency in HTTP handlers.
    Prefer `core_platform.data_management.db_async.get_async_session` for
    request-time database access. This sync session helper remains available
    for non-HTTP service code paths and background jobs.
    """
    warnings.warn(
        "database_init.get_db_session is deprecated for FastAPI handlers; "
        "use core_platform.data_management.db_async.get_async_session instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if not _database_initializer:
        raise RuntimeError("Database not initialized")
    
    db = _database_initializer.get_session()
    try:
        yield db
    finally:
        db.close()
