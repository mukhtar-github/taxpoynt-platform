"""
SI Services - IRN & QR Code Generation Module

Handles Invoice Reference Number (IRN) generation and QR code creation for System Integrator role.
Manages IRN lifecycle, bulk processing, and QR code generation for invoice verification.
"""

# New granular components
from .irn_generator import IRNGenerator
from .qr_code_generator import QRCodeGenerator
from .sequence_manager import SequenceManager
from .duplicate_detector import DuplicateDetector
from .irn_validator import IRNValidator
from .bulk_processor import BulkProcessor

# Services
from .irn_generation_service import IRNGenerationService

__all__ = [
    # New granular components
    "IRNGenerator",
    "QRCodeGenerator", 
    "SequenceManager",
    "DuplicateDetector",
    "IRNValidator",
    "BulkProcessor",
    
    # Refactored services
    "IRNGenerationService",
]
