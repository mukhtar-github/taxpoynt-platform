"""
Authentication Database Integration
==================================
Connects the auth router to existing SQLAlchemy models and database infrastructure.
Replaces in-memory storage with proper database operations.
"""

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, timezone

# Import existing models
from core_platform.data_management.models.user import User, UserRole
from core_platform.data_management.models.organization import Organization, BusinessType, OrganizationStatus
from core_platform.data_management.models.oauth_client import OAuthClient, OAuthClientStatus
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
        """Create tables using existing models and handle migrations."""
        try:
            # Create all tables (this is safe for existing tables)
            BaseModel.metadata.create_all(bind=self.engine)
            
            # Handle organization_id column migration
            self._migrate_organization_id_column()
            
            logger.info("Database tables created/migrated successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def _migrate_organization_id_column(self):
        """Add all new columns to users and organizations tables if they don't exist."""
        try:
            with self.engine.connect() as conn:
                # Define all new columns for users table
                user_migrations = [
                    ("organization_id", "UUID"),
                    ("is_deleted", "BOOLEAN DEFAULT FALSE"),
                    ("deleted_at", "TIMESTAMP WITH TIME ZONE"),
                    ("deleted_by", "UUID"),
                    ("deletion_reason", "VARCHAR(255)"),
                    ("scheduled_hard_delete_at", "TIMESTAMP WITH TIME ZONE"),
                    ("last_activity_at", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
                ]
                
                # Define all new columns for organizations table  
                org_migrations = [
                    ("is_deleted", "BOOLEAN DEFAULT FALSE"),
                    ("deleted_at", "TIMESTAMP WITH TIME ZONE"),
                    ("deleted_by", "UUID"),
                    ("deletion_reason", "VARCHAR(255)"),
                    ("scheduled_hard_delete_at", "TIMESTAMP WITH TIME ZONE")
                ]
                
                # Migrate users table
                self._migrate_table_columns(conn, "users", user_migrations)
                
                # Migrate organizations table
                self._migrate_table_columns(conn, "organizations", org_migrations)
                
                # Create indexes
                indexes = [
                    "CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users(organization_id)",
                    "CREATE INDEX IF NOT EXISTS ix_users_is_deleted ON users(is_deleted)", 
                    "CREATE INDEX IF NOT EXISTS ix_organizations_is_deleted ON organizations(is_deleted)"
                ]
                
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        conn.commit()
                        logger.debug(f"Created index: {index_sql}")
                    except Exception as idx_e:
                        logger.warning(f"Could not create index: {idx_e}")
                
                conn.commit()
                logger.info("✅ Database migration completed successfully")
                    
        except Exception as e:
            # If we're using SQLite or the columns already exist, it's fine
            logger.warning(f"Could not complete database migration (this is normal for SQLite): {e}")
    
    def _migrate_table_columns(self, conn, table_name: str, columns: list):
        """Helper method to migrate columns for a specific table."""
        for column_name, column_type in columns:
            try:
                if self._column_exists(conn, table_name, column_name):
                    logger.debug(f"Column {column_name} already exists in {table_name}")
                    continue

                logger.info(f"Adding {column_name} column to {table_name} table...")

                sqlite_type = self._convert_to_sqlite_type(column_type)

                conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sqlite_type}"))
                conn.commit()

                if "sqlite" in self.database_url.lower() and column_name == "last_activity_at":
                    conn.execute(text(f"UPDATE {table_name} SET {column_name} = CURRENT_TIMESTAMP WHERE {column_name} IS NULL"))
                    conn.commit()

                logger.info(f"✅ Added {column_name} to {table_name}")

            except Exception as e:
                logger.warning(f"Could not add {column_name} to {table_name}: {e}")
    
    def _column_exists(self, conn, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table (database-agnostic)."""
        try:
            if "sqlite" in self.database_url.lower():
                # For SQLite, use PRAGMA table_info
                result = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
                return any(row[1] == column_name for row in result)
            else:
                # For PostgreSQL, use information_schema
                result = conn.execute(
                    text("SELECT column_name FROM information_schema.columns WHERE table_name=:table AND column_name=:column"),
                    {"table": table_name, "column": column_name}
                ).fetchone()
                return result is not None
        except Exception as e:
            logger.debug(f"Error checking column existence: {e}")
            return False
    
    def _convert_to_sqlite_type(self, pg_type: str) -> str:
        """Convert PostgreSQL column types to SQLite types."""
        if "sqlite" not in self.database_url.lower():
            return pg_type
            
        # Convert PostgreSQL types to SQLite equivalents
        type_mappings = {
            "UUID": "TEXT",
            "BOOLEAN DEFAULT FALSE": "INTEGER DEFAULT 0",
            "TIMESTAMP WITH TIME ZONE": "DATETIME",
            "TIMESTAMP WITH TIME ZONE DEFAULT NOW()": "DATETIME",  # Remove default for SQLite
            "VARCHAR(255)": "TEXT"
        }
        
        return type_mappings.get(pg_type, pg_type)
    
    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    # ------------------------------------------------------------------
    # OAuth client helpers
    # ------------------------------------------------------------------

    def list_oauth_clients(self) -> List[OAuthClient]:
        session = self.get_session()
        try:
            return session.query(OAuthClient).all()
        except Exception as exc:
            logger.error(f"Failed to list OAuth clients: {exc}")
            return []
        finally:
            session.close()

    def get_oauth_client_by_client_id(self, client_id: str) -> Optional[OAuthClient]:
        session = self.get_session()
        try:
            return (
                session.query(OAuthClient)
                .filter(OAuthClient.client_id == client_id)
                .one_or_none()
            )
        except Exception as exc:
            logger.error(f"Failed to load OAuth client {client_id}: {exc}")
            return None
        finally:
            session.close()

    def upsert_oauth_client(
        self,
        *,
        client_id: str,
        client_secret_hash: str,
        client_name: str,
        allowed_grant_types: List[str],
        allowed_scopes: List[str],
        redirect_uris: List[str],
        is_confidential: bool,
        status: OAuthClientStatus,
        metadata: Dict[str, Any],
    ) -> OAuthClient:
        session = self.get_session()
        try:
            client = (
                session.query(OAuthClient)
                .filter(OAuthClient.client_id == client_id)
                .one_or_none()
            )

            if client is None:
                client = OAuthClient(
                    client_id=client_id,
                    client_secret_hash=client_secret_hash,
                    client_name=client_name,
                    allowed_grant_types=allowed_grant_types,
                    allowed_scopes=allowed_scopes,
                    redirect_uris=redirect_uris,
                    is_confidential=is_confidential,
                    status=status,
                    metadata_blob=metadata,
                )
                session.add(client)
            else:
                client.client_secret_hash = client_secret_hash
                client.client_name = client_name
                client.allowed_grant_types = allowed_grant_types
                client.allowed_scopes = allowed_scopes
                client.redirect_uris = redirect_uris
                client.is_confidential = is_confidential
                client.status = status
                client.client_metadata = metadata

            session.commit()
            session.refresh(client)
            return client
        except Exception as exc:
            session.rollback()
            logger.error(f"Failed to upsert OAuth client {client_id}: {exc}")
            raise
        finally:
            session.close()
    
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
            
            # Create User instance with proper type conversion
            import uuid
            from datetime import datetime
            
            # Convert organization_id to UUID if it's a string
            org_id = user_data.get("organization_id")
            if org_id and isinstance(org_id, str):
                try:
                    org_id = uuid.UUID(org_id)
                except ValueError:
                    org_id = None
            
            user = User(
                email=user_data["email"],
                hashed_password=user_data["hashed_password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone=user_data.get("phone"),
                role=service_role_mapping.get(user_data["service_package"], UserRole.SI_USER),
                service_package=user_data["service_package"],
                organization_id=org_id,
                is_active=True,
                is_email_verified=False,
                terms_accepted_at=user_data.get("terms_accepted_at"),
                privacy_accepted_at=user_data.get("privacy_accepted_at")
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
                "email_verification_token": user.email_verification_token,
                "email_verification_sent_at": user.email_verification_sent_at.isoformat() if user.email_verification_sent_at else None,
                "organization_id": str(user.organization_id) if user.organization_id else None,
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
            # Convert owner_id to UUID if it's a string
            owner_id = org_data.get("owner_id")
            if owner_id and isinstance(owner_id, str):
                try:
                    owner_id = uuid.UUID(owner_id)
                except ValueError:
                    owner_id = None
            else:
                owner_id = None
            
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
    
    def get_user_by_email(self, email: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """Get user by email using existing User model."""
        session = self.get_session()
        try:
            query = session.query(User).filter(User.email == email)
            
            # By default, exclude soft-deleted users
            if not include_deleted:
                query = query.filter(User.is_deleted == False)
                
            user = query.first()
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
                "email_verification_token": user.email_verification_token,
                "email_verification_sent_at": user.email_verification_sent_at.isoformat() if user.email_verification_sent_at else None,
                "organization_id": str(user.organization_id) if user.organization_id else None,
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
    
    def get_user_by_id(self, user_id: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """Get user by ID using existing User model."""
        session = self.get_session()
        try:
            # Ensure UUID type for comparison
            import uuid as _uuid
            _user_id = user_id
            if isinstance(user_id, str):
                try:
                    _user_id = _uuid.UUID(user_id)
                except ValueError:
                    _user_id = user_id

            query = session.query(User).filter(User.id == _user_id)
            
            # By default, exclude soft-deleted users
            if not include_deleted:
                query = query.filter(User.is_deleted == False)
                
            user = query.first()
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
                "organization_id": str(user.organization_id) if user.organization_id else None,
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
            # Ensure UUID type for comparison
            import uuid as _uuid
            _org_id = org_id
            if isinstance(org_id, str):
                try:
                    _org_id = _uuid.UUID(org_id)
                except ValueError:
                    _org_id = org_id

            org = session.query(Organization).filter(Organization.id == _org_id).first()
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
            # Ensure UUID type for comparison
            import uuid as _uuid
            _user_id = user_id
            if isinstance(user_id, str):
                try:
                    _user_id = _uuid.UUID(user_id)
                except ValueError:
                    _user_id = user_id

            user = session.query(User).filter(User.id == _user_id).first()
            if user:
                user.last_login = datetime.now(timezone.utc)
                user.login_count = (user.login_count or 0) + 1
                user.updated_at = datetime.now(timezone.utc)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating user login: {e}")
        finally:
            session.close()

    def set_email_verification_token(self, user_id: str, token_hash: str) -> None:
        """Store hashed email verification token and timestamp."""
        session = self.get_session()
        try:
            import uuid as _uuid
            from datetime import datetime, timezone

            _user_id = user_id
            if isinstance(user_id, str):
                try:
                    _user_id = _uuid.UUID(user_id)
                except ValueError:
                    _user_id = user_id

            user = session.query(User).filter(User.id == _user_id).first()
            if not user:
                raise ValueError("User not found")

            user.email_verification_token = token_hash
            user.email_verification_sent_at = datetime.now(timezone.utc)
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error(f"Error setting email verification token: {exc}")
            raise
        finally:
            session.close()

    def mark_email_verified(self, user_id: str,
                             terms_accepted: bool = False,
                             privacy_accepted: bool = False) -> Dict[str, Any]:
        """Mark user as email verified and update consent timestamps."""
        session = self.get_session()
        try:
            import uuid as _uuid
            from datetime import datetime, timezone

            _user_id = user_id
            if isinstance(user_id, str):
                try:
                    _user_id = _uuid.UUID(user_id)
                except ValueError:
                    _user_id = user_id

            user = session.query(User).filter(User.id == _user_id).first()
            if not user:
                raise ValueError("User not found")

            now = datetime.now(timezone.utc)
            user.is_email_verified = True
            user.email_verification_token = None
            user.email_verification_sent_at = None

            if terms_accepted:
                user.terms_accepted_at = now
            if privacy_accepted:
                user.privacy_accepted_at = now

            session.commit()
            session.refresh(user)

            return {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "service_package": user.service_package,
                "is_email_verified": user.is_email_verified,
                "organization_id": str(user.organization_id) if user.organization_id else None,
            }
        except Exception as exc:
            session.rollback()
            logger.error(f"Error marking email verified: {exc}")
            raise
        finally:
            session.close()
    
    def update_organization_owner(self, org_id: str, user_id: str) -> None:
        """Update organization owner."""
        session = self.get_session()
        try:
            # Ensure UUID type for comparison
            import uuid as _uuid
            _org_id = org_id
            if isinstance(org_id, str):
                try:
                    _org_id = _uuid.UUID(org_id)
                except ValueError:
                    _org_id = org_id

            org = session.query(Organization).filter(Organization.id == _org_id).first()
            if org:
                # Note: Organization model might need owner_id field added
                # For now, just update the updated_at timestamp
                org.updated_at = datetime.now(timezone.utc)
                session.commit()
                logger.info(f"Organization {org_id} owner updated to user {user_id}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating organization owner: {e}")
        finally:
            session.close()
    
    def get_all_users(self, include_deleted: bool = False, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all users with pagination (for admin dashboard)."""
        session = self.get_session()
        try:
            query = session.query(User)
            
            if not include_deleted:
                query = query.filter(User.is_deleted == False)
                
            users = query.offset(offset).limit(limit).all()
            
            return [{
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "service_package": user.service_package,
                "is_active": user.is_active,
                "is_deleted": user.is_deleted,
                "organization_id": str(user.organization_id) if user.organization_id else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            } for user in users]
            
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            raise
        finally:
            session.close()
    
    def soft_delete_user(self, user_id: str, deleted_by_user_id: str, reason: str = None) -> bool:
        """Soft delete a user (admin function)."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False
                
            user.soft_delete(deleted_by_user_id, reason)
            session.commit()
            
            logger.info(f"User {user_id} soft deleted by {deleted_by_user_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error soft deleting user: {e}")
            raise
        finally:
            session.close()
    
    def restore_user(self, user_id: str) -> bool:
        """Restore a soft-deleted user (admin function)."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user or not user.is_deleted:
                return False
                
            user.restore()
            session.commit()
            
            logger.info(f"User {user_id} restored")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error restoring user: {e}")
            raise
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
