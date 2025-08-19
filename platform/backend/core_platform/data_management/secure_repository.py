"""
TaxPoynt Platform - Secure Data Repository
==========================================
Data access layer with automatic encryption/decryption for sensitive fields.
Integrates with ProductionJWTManager for secure credential storage.
"""

import logging
from typing import Dict, Any, Optional, List, Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from core_platform.security import get_jwt_manager
from .models.banking import BankingConnection, BankingCredentials
from .models.business_systems import Certificate

logger = logging.getLogger(__name__)

# Type variable for repository classes
T = TypeVar('T')


class SecureRepository:
    """
    Base repository class with automatic encryption/decryption for sensitive fields.
    
    Features:
    - Automatic encryption of sensitive data before database storage
    - Automatic decryption when retrieving sensitive data
    - Secure credential management using ProductionJWTManager
    - Error handling and logging for security operations
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.jwt_manager = get_jwt_manager()
        
        # Define sensitive fields for each model
        self.sensitive_fields = {
            BankingConnection: ['access_token', 'refresh_token'],
            BankingCredentials: ['api_key', 'client_id', 'client_secret', 'webhook_secret'],
            Certificate: ['private_key', 'certificate_data']
        }
    
    def _encrypt_sensitive_fields(self, model_instance: Any) -> None:
        """Encrypt sensitive fields before saving to database"""
        try:
            model_class = type(model_instance)
            sensitive_fields = self.sensitive_fields.get(model_class, [])
            
            for field_name in sensitive_fields:
                if hasattr(model_instance, field_name):
                    field_value = getattr(model_instance, field_name)
                    
                    if field_value and isinstance(field_value, str):
                        # Only encrypt if not already encrypted (basic check)
                        if not field_value.startswith('gAAA'):  # Fernet encryption prefix
                            encrypted_value = self.jwt_manager.encrypt_sensitive_data(field_value)
                            setattr(model_instance, field_name, encrypted_value)
                            logger.debug(f"Encrypted field {field_name} for {model_class.__name__}")
                            
        except Exception as e:
            logger.error(f"Error encrypting sensitive fields: {e}")
            raise ValueError(f"Failed to encrypt sensitive data: {str(e)}")
    
    def _decrypt_sensitive_fields(self, model_instance: Any) -> None:
        """Decrypt sensitive fields after retrieving from database"""
        try:
            model_class = type(model_instance)
            sensitive_fields = self.sensitive_fields.get(model_class, [])
            
            for field_name in sensitive_fields:
                if hasattr(model_instance, field_name):
                    field_value = getattr(model_instance, field_name)
                    
                    if field_value and isinstance(field_value, str):
                        # Only decrypt if appears to be encrypted
                        if field_value.startswith('gAAA'):  # Fernet encryption prefix
                            try:
                                decrypted_value = self.jwt_manager.decrypt_sensitive_data(field_value)
                                setattr(model_instance, field_name, decrypted_value)
                                logger.debug(f"Decrypted field {field_name} for {model_class.__name__}")
                            except Exception as e:
                                logger.warning(f"Failed to decrypt field {field_name}: {e}")
                                # Keep encrypted value if decryption fails
                                
        except Exception as e:
            logger.error(f"Error decrypting sensitive fields: {e}")
            # Don't raise exception for decryption errors - continue with encrypted data
    
    def create(self, model_class: Type[T], **kwargs) -> T:
        """Create new record with automatic encryption of sensitive fields"""
        try:
            # Create model instance
            instance = model_class(**kwargs)
            
            # Encrypt sensitive fields
            self._encrypt_sensitive_fields(instance)
            
            # Save to database
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            
            # Decrypt for return
            self._decrypt_sensitive_fields(instance)
            
            logger.info(f"Created {model_class.__name__} with ID {getattr(instance, 'id', 'unknown')}")
            return instance
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating {model_class.__name__}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {model_class.__name__}: {e}")
            raise
    
    def get_by_id(self, model_class: Type[T], record_id: str) -> Optional[T]:
        """Get record by ID with automatic decryption"""
        try:
            instance = self.db.query(model_class).filter(model_class.id == record_id).first()
            
            if instance:
                self._decrypt_sensitive_fields(instance)
                logger.debug(f"Retrieved {model_class.__name__} with ID {record_id}")
            
            return instance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving {model_class.__name__} {record_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving {model_class.__name__} {record_id}: {e}")
            raise
    
    def get_all(self, model_class: Type[T], limit: int = 100) -> List[T]:
        """Get all records with automatic decryption"""
        try:
            instances = self.db.query(model_class).limit(limit).all()
            
            for instance in instances:
                self._decrypt_sensitive_fields(instance)
            
            logger.debug(f"Retrieved {len(instances)} {model_class.__name__} records")
            return instances
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving {model_class.__name__} records: {e}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving {model_class.__name__} records: {e}")
            raise
    
    def update(self, model_class: Type[T], record_id: str, **kwargs) -> Optional[T]:
        """Update record with automatic encryption of sensitive fields"""
        try:
            instance = self.db.query(model_class).filter(model_class.id == record_id).first()
            
            if not instance:
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            
            # Encrypt sensitive fields
            self._encrypt_sensitive_fields(instance)
            
            # Save to database
            self.db.commit()
            self.db.refresh(instance)
            
            # Decrypt for return
            self._decrypt_sensitive_fields(instance)
            
            logger.info(f"Updated {model_class.__name__} with ID {record_id}")
            return instance
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating {model_class.__name__} {record_id}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {model_class.__name__} {record_id}: {e}")
            raise
    
    def delete(self, model_class: Type[T], record_id: str) -> bool:
        """Delete record by ID"""
        try:
            instance = self.db.query(model_class).filter(model_class.id == record_id).first()
            
            if not instance:
                return False
            
            self.db.delete(instance)
            self.db.commit()
            
            logger.info(f"Deleted {model_class.__name__} with ID {record_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting {model_class.__name__} {record_id}: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting {model_class.__name__} {record_id}: {e}")
            raise


class BankingRepository(SecureRepository):
    """Repository for banking-related models with secure credential management"""
    
    def create_banking_connection(
        self,
        si_id: str,
        provider: str,
        provider_connection_id: str,
        access_token: str = None,
        refresh_token: str = None,
        **kwargs
    ) -> BankingConnection:
        """Create banking connection with secure token storage"""
        return self.create(
            BankingConnection,
            si_id=si_id,
            provider=provider,
            provider_connection_id=provider_connection_id,
            access_token=access_token,
            refresh_token=refresh_token,
            **kwargs
        )
    
    def create_banking_credentials(
        self,
        si_id: str,
        provider: str,
        api_key: str = None,
        client_id: str = None,
        client_secret: str = None,
        webhook_secret: str = None,
        **kwargs
    ) -> BankingCredentials:
        """Create banking credentials with secure encryption"""
        return self.create(
            BankingCredentials,
            si_id=si_id,
            provider=provider,
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret,
            webhook_secret=webhook_secret,
            **kwargs
        )
    
    def get_active_connections_by_si(self, si_id: str) -> List[BankingConnection]:
        """Get all active banking connections for SI"""
        try:
            connections = self.db.query(BankingConnection).filter(
                BankingConnection.si_id == si_id,
                BankingConnection.status == 'CONNECTED'
            ).all()
            
            for connection in connections:
                self._decrypt_sensitive_fields(connection)
            
            return connections
            
        except Exception as e:
            logger.error(f"Error retrieving connections for SI {si_id}: {e}")
            raise
    
    def get_credentials_by_provider(self, si_id: str, provider: str) -> Optional[BankingCredentials]:
        """Get banking credentials for specific provider"""
        try:
            credentials = self.db.query(BankingCredentials).filter(
                BankingCredentials.si_id == si_id,
                BankingCredentials.provider == provider,
                BankingCredentials.is_active == True
            ).first()
            
            if credentials:
                self._decrypt_sensitive_fields(credentials)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Error retrieving credentials for SI {si_id}, provider {provider}: {e}")
            raise


def get_secure_repository(db_session: Session) -> SecureRepository:
    """Factory function to get secure repository instance"""
    return SecureRepository(db_session)


def get_banking_repository(db_session: Session) -> BankingRepository:
    """Factory function to get banking repository instance"""
    return BankingRepository(db_session)