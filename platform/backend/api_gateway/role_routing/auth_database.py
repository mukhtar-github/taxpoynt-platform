"""
Authentication Database Integration
==================================
Connects the auth router to existing SQLAlchemy models and database infrastructure.
Replaces in-memory storage with proper database operations.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# Import existing models
from core_platform.data_management.models.user import User, UserRole
from core_platform.data_management.models.organization import Organization, BusinessType, OrganizationStatus
from core_platform.data_management.models.base import BaseModel

logger = logging.getLogger(__name__)

class AuthDatabaseManager:
    """Database manager for authentication operations using existing SQLAlchemy models."""
    
    def __init__(self, database_url: str = None):
        """Initialize database connection using existing infrastructure patterns."""
        import os
        
        # Use Railway PostgreSQL database URL
        railway_db_url = os.getenv("DATABASE_URL") or os.getenv("PGDATABASE")
        if railway_db_url and railway_db_url.startswith("postgres://"):
            railway_db_url = railway_db_url.replace("postgres://", "postgresql://", 1)
            
        self.database_url = database_url or railway_db_url or "sqlite:///taxpoynt_auth.db"  # PostgreSQL first, SQLite fallback
        
        logger.info(f"🔗 AuthDatabase connecting to: {'PostgreSQL' if 'postgresql://' in self.database_url else 'SQLite'}")
        
        # Create engine using patterns from existing database manager
        self.engine = create_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create session maker
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        self._create_tables()
    
    def _create_tables(self):
        """Create tables using existing models."""
        try:
            BaseModel.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user using existing User model."""
        session = self.get_session()
        try:
            # Map service package to user role
            service_role_mapping = {
                "si": UserRole.SI_USER,
                "app": UserRole.APP_USER, 
                "hybrid": UserRole.HYBRID_USER
            }
            
            # Create User instance
            user = User(
                email=user_data["email"],
                hashed_password=user_data["hashed_password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone=user_data.get("phone"),
                role=service_role_mapping.get(user_data["service_package"], UserRole.SI_USER),
                service_package=user_data["service_package"],
                is_active=True,
                is_email_verified=False
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            # Return user data in expected format
            return {
                "id": str(user.id),
                "email": user.email,
                "hashed_password": user.hashed_password,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role.value,
                "service_package": user.service_package,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified,
                "organization_id": str(user_data.get("organization_id")) if user_data.get("organization_id") else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": None,
                "login_count": 0
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            raise
        finally:
            session.close()
    
    def create_organization(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new organization using existing Organization model."""
        session = self.get_session()
        try:
            # Map business type string to enum if provided
            business_type = None
            if org_data.get("business_type"):
                # Simple mapping - could be enhanced
                business_type_mapping = {
                    "Technology": BusinessType.LIMITED_COMPANY,
                    "Technology Services": BusinessType.LIMITED_COMPANY,
                    "Services": BusinessType.LIMITED_COMPANY,
                    "Manufacturing": BusinessType.LIMITED_COMPANY,
                    "Retail": BusinessType.LIMITED_COMPANY
                }
                business_type = business_type_mapping.get(
                    org_data["business_type"], 
                    BusinessType.LIMITED_COMPANY
                )
            
            # Create Organization instance
            organization = Organization(
                name=org_data["name"],
                business_name=org_data["name"],
                business_type=business_type,
                tin=org_data.get("tin"),
                rc_number=org_data.get("rc_number"),
                email=org_data.get("email"),
                phone=org_data.get("phone"),
                address=org_data.get("address"),
                status=OrganizationStatus.ACTIVE
            )
            
            session.add(organization)
            session.commit()
            session.refresh(organization)
            
            # Return organization data in expected format
            return {
                "id": str(organization.id),
                "name": organization.name,
                "business_type": organization.business_type.value if organization.business_type else None,
                "tin": organization.tin,
                "rc_number": organization.rc_number,
                "address": organization.address,
                "status": organization.status.value,
                "owner_id": org_data.get("owner_id"),
                "service_packages": org_data.get("service_packages", []),
                "created_at": organization.created_at.isoformat() if organization.created_at else None,
                "updated_at": organization.updated_at.isoformat() if organization.updated_at else None
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating organization: {e}")
            raise
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email using existing User model."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                return None
            
            return {
                "id": str(user.id),
                "email": user.email,
                "hashed_password": user.hashed_password,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role.value,
                "service_package": user.service_package,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified,
                "organization_id": None,  # TODO: Add relationship
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": None,
                "login_count": 0
            }
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID using existing User model."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            return {
                "id": str(user.id),
                "email": user.email,
                "hashed_password": user.hashed_password,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone": user.phone,
                "role": user.role.value,
                "service_package": user.service_package,
                "is_active": user.is_active,
                "is_email_verified": user.is_email_verified,
                "organization_id": None,  # TODO: Add relationship
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "last_login": None,
                "login_count": 0
            }
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise
        finally:
            session.close()
    
    def get_organization_by_id(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization by ID using existing Organization model."""
        session = self.get_session()
        try:
            org = session.query(Organization).filter(Organization.id == org_id).first()
            if not org:
                return None
                
            return {
                "id": str(org.id),
                "name": org.name,
                "business_type": org.business_type.value if org.business_type else "Technology",
                "tin": org.tin,
                "rc_number": org.rc_number,
                "status": org.status.value,
                "service_packages": ["si"],  # TODO: Add proper relationship
                "created_at": org.created_at.isoformat() if org.created_at else None,
                "updated_at": org.updated_at.isoformat() if org.updated_at else None
            }
        except Exception as e:
            logger.error(f"Error getting organization by ID: {e}")
            raise
        finally:
            session.close()
    
    def update_user_login(self, user_id: str) -> None:
        """Update user login timestamp and count."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                # TODO: Add last_login and login_count fields to User model
                # For now, just update the updated_at timestamp
                user.updated_at = datetime.now(timezone.utc)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user login: {e}")
        finally:
            session.close()


# Global database manager instance
auth_db_manager: Optional[AuthDatabaseManager] = None

def get_auth_database() -> AuthDatabaseManager:
    """Get global auth database manager instance."""
    global auth_db_manager
    if auth_db_manager is None:
        auth_db_manager = AuthDatabaseManager()
    return auth_db_manager

def initialize_auth_database(database_url: str = None) -> AuthDatabaseManager:
    """Initialize auth database with specific URL."""
    global auth_db_manager
    auth_db_manager = AuthDatabaseManager(database_url)
    return auth_db_manager