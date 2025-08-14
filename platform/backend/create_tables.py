#!/usr/bin/env python3
"""
PostgreSQL Table Creation Script
===============================
Automatically generates PostgreSQL tables from SQLAlchemy models.
Standalone script that avoids complex dependency chains.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Create PostgreSQL tables from SQLAlchemy models."""
    
    print('🗄️  AUTOMATIC POSTGRESQL TABLE GENERATION')
    print('='*50)
    
    try:
        # Import dependencies
        from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Enum, ForeignKey, Text, JSON
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.orm import relationship
        from sqlalchemy.dialects.postgresql import UUID
        from datetime import datetime
        import uuid
        import enum
        
        # Create base
        Base = declarative_base()
        
        # Define enums
        class UserRole(enum.Enum):
            SI_USER = "si_user"
            APP_USER = "app_user"  
            HYBRID_USER = "hybrid_user"
            BUSINESS_OWNER = "business_owner"
            BUSINESS_ADMIN = "business_admin"
            BUSINESS_USER = "business_user"
            PLATFORM_ADMIN = "platform_admin"
            SUPPORT_USER = "support_user"
        
        class BusinessType(enum.Enum):
            SOLE_PROPRIETORSHIP = "sole_proprietorship"
            PARTNERSHIP = "partnership" 
            LIMITED_COMPANY = "limited_company"
            PUBLIC_COMPANY = "public_company"
            NON_PROFIT = "non_profit"
            COOPERATIVE = "cooperative"
        
        class OrganizationStatus(enum.Enum):
            ACTIVE = "active"
            INACTIVE = "inactive"
            SUSPENDED = "suspended"
            PENDING_VERIFICATION = "pending_verification"
        
        # Define User model
        class User(Base):
            __tablename__ = "users"
            
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
            email = Column(String(255), unique=True, index=True, nullable=False)
            hashed_password = Column(String(255), nullable=False)
            
            # Personal information
            first_name = Column(String(100), nullable=True)
            last_name = Column(String(100), nullable=True)
            phone = Column(String(20), nullable=True)
            
            # Account status
            is_active = Column(Boolean, default=True, nullable=False)
            is_email_verified = Column(Boolean, default=False, nullable=False)
            
            # Role and service
            role = Column(Enum(UserRole), default=UserRole.SI_USER, nullable=False)
            service_package = Column(String(20), default="si", nullable=False)
            
            # Timestamps
            created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
        
        # Define Organization model
        class Organization(Base):
            __tablename__ = "organizations"
            
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
            name = Column(String(255), nullable=False, index=True)
            business_name = Column(String(255), nullable=True)
            
            # Business details
            business_type = Column(Enum(BusinessType), nullable=True)
            tin = Column(String(50), nullable=True, index=True)
            rc_number = Column(String(50), nullable=True, index=True)
            vat_number = Column(String(50), nullable=True)
            
            # Contact information
            email = Column(String(255), nullable=True)
            phone = Column(String(20), nullable=True)
            address = Column(Text, nullable=True)
            
            # Status
            status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE, nullable=False)
            
            # Timestamps
            created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
        
        # Database connection
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            # Fallback to SQLite for development
            database_url = 'sqlite:///taxpoynt_platform.db'
            print(f'📄 Using SQLite: {database_url}')
        else:
            print(f'🐘 Using PostgreSQL: {database_url[:30]}...')
        
        # Create engine
        engine = create_engine(database_url, echo=True)
        
        # Create all tables
        print('⚡ Creating tables from SQLAlchemy models...')
        Base.metadata.create_all(bind=engine)
        
        print('✅ Tables created successfully!')
        print()
        print('📋 Generated Tables:')
        print('   • users (User authentication & profiles)')
        print('   • organizations (Business entities & details)')
        print()
        
        # Test connection
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if tables exist
        user_count = session.query(User).count()
        org_count = session.query(Organization).count()
        
        print(f'📊 Database Status:')
        print(f'   • Users: {user_count}')
        print(f'   • Organizations: {org_count}')
        print()
        print('🎯 Database ready for production user registration!')
        
        session.close()
        return True
        
    except ImportError as e:
        print(f'❌ Import error: {e}')
        print('💡 Install required dependencies: pip install sqlalchemy psycopg2-binary')
        return False
    except Exception as e:
        print(f'❌ Error creating tables: {e}')
        return False

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)