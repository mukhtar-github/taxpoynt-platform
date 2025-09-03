"""
API Versions - Shared Models
============================
Central import point for all API version models.
Provides backward compatibility and consistent import paths.
"""

# Import v1 models for backward compatibility
from .v1.version_models import (
    V1ResponseModel,
    V1ErrorModel,
    V1PaginationModel,
    V1BusinessSystemInfo
)

# Export for direct import
__all__ = [
    'V1ResponseModel',
    'V1ErrorModel', 
    'V1PaginationModel',
    'V1BusinessSystemInfo'
]
