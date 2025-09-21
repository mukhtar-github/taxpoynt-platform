"""
TaxPoynt Platform - Database Base Model
======================================
Base SQLAlchemy model with common functionality for all platform models.
"""

try:
    # SQLAlchemy 2.x
    from sqlalchemy.orm import declarative_base
except ImportError:  # pragma: no cover - fallback for older SQLAlchemy
    from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
from typing import Any
import uuid

Base = declarative_base()

class TimestampMixin:
    """Mixin for models that need timestamp tracking."""
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

class BaseModel(Base, TimestampMixin):
    """Base model with common functionality."""
    
    __abstract__ = True
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model instance from dictionary."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
