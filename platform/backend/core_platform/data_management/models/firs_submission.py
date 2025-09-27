"""
TaxPoynt Platform - FIRS Submission Models
=========================================
Models for managing FIRS e-invoice submissions and compliance.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, Text, JSON, DateTime, Integer, Numeric, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

class SubmissionStatus(enum.Enum):
    """FIRS submission status."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"

class InvoiceType(enum.Enum):
    """Types of invoices for FIRS submission."""
    
    STANDARD_INVOICE = "standard_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    SIMPLIFIED_INVOICE = "simplified_invoice"
    RECEIPT = "receipt"

class ValidationStatus(enum.Enum):
    """Validation status for submissions."""
    
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"

class FIRSSubmission(BaseModel):
    """FIRS e-invoice submission tracking."""
    
    __tablename__ = "firs_submissions"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Invoice identification
    invoice_number = Column(String(100), nullable=False, index=True)
    invoice_type = Column(Enum(InvoiceType), default=InvoiceType.STANDARD_INVOICE, nullable=False)
    irn = Column(String(255), nullable=True, unique=True, index=True)  # Invoice Reference Number from FIRS
    csid = Column(String(255), nullable=True, index=True)  # Cryptographic Stamp Identifier from FIRS
    csid_hash = Column(String(512), nullable=True)
    qr_payload = Column(JSON, nullable=True)  # QR payload returned by FIRS
    firs_stamp_metadata = Column(JSON, nullable=True)  # Additional stamp metadata from FIRS
    
    # Submission details
    status = Column(Enum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    validation_status = Column(Enum(ValidationStatus), default=ValidationStatus.PENDING, nullable=False)
    
    # Invoice data
    invoice_data = Column(JSON, nullable=False)  # Complete invoice data in UBL format
    original_data = Column(JSON, nullable=True)  # Original ERP data before transformation
    
    # Financial details
    subtotal = Column(Numeric(15, 2), nullable=True)
    tax_amount = Column(Numeric(15, 2), nullable=True)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="NGN", nullable=False)
    
    # Customer information
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_tin = Column(String(50), nullable=True, index=True)
    
    # FIRS response
    firs_response = Column(JSON, nullable=True)  # Complete FIRS API response
    firs_submission_id = Column(String(100), nullable=True, index=True)  # FIRS internal ID
    firs_status_code = Column(String(20), nullable=True)
    firs_message = Column(Text, nullable=True)
    firs_received_at = Column(DateTime(timezone=True), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_details = Column(JSON, nullable=True)  # Detailed error information
    retry_count = Column(Integer, default=0, nullable=False)
    last_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Integration source
    source_integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=True)
    source_system = Column(String(50), nullable=True)  # ERP system that generated the invoice
    
    # Audit trail
    submitted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="firs_submissions")
    source_integration = relationship("Integration", foreign_keys=[source_integration_id])
    submitted_by = relationship("User", foreign_keys=[submitted_by_user_id])
    
    @property
    def is_successful(self) -> bool:
        """Check if submission was successful."""
        return self.status in [SubmissionStatus.SUBMITTED, SubmissionStatus.ACCEPTED]
    
    @property
    def is_failed(self) -> bool:
        """Check if submission failed."""
        return self.status in [SubmissionStatus.REJECTED, SubmissionStatus.FAILED]
    
    @property
    def is_pending(self) -> bool:
        """Check if submission is still pending."""
        return self.status in [SubmissionStatus.PENDING, SubmissionStatus.PROCESSING]
    
    @property
    def can_retry(self) -> bool:
        """Check if submission can be retried."""
        return (self.is_failed and 
                self.retry_count < 3 and
                self.status != SubmissionStatus.CANCELLED)
    
    @property
    def processing_time_minutes(self) -> float:
        """Get processing time in minutes."""
        if self.submitted_at and self.accepted_at:
            delta = self.accepted_at - self.submitted_at
            return delta.total_seconds() / 60
        return None
    
    def get_validation_errors(self) -> list:
        """Get list of validation errors."""
        if (self.error_details and 
            isinstance(self.error_details, dict) and 
            'validation_errors' in self.error_details):
            return self.error_details['validation_errors']
        return []
    
    def get_firs_errors(self) -> list:
        """Get list of FIRS-specific errors."""
        if (self.error_details and 
            isinstance(self.error_details, dict) and 
            'firs_errors' in self.error_details):
            return self.error_details['firs_errors']
        return []
    
    def update_status(self, new_status: SubmissionStatus, message: str = None, firs_data: dict = None):
        """Update submission status with optional message and FIRS data."""
        self.status = new_status
        
        if message:
            self.firs_message = message
            
        if firs_data:
            self.firs_response = firs_data
            self.firs_submission_id = firs_data.get('submissionId')
            self.firs_status_code = firs_data.get('statusCode')
            if 'irn' in firs_data:
                self.irn = firs_data['irn']
            if 'csid' in firs_data:
                self.csid = firs_data['csid']
            if 'csidHash' in firs_data:
                self.csid_hash = firs_data['csidHash']
            if 'qr' in firs_data:
                self.qr_payload = firs_data['qr']
            elif 'qr_code' in firs_data:
                self.qr_payload = firs_data['qr_code']
            if 'stampMetadata' in firs_data:
                self.firs_stamp_metadata = firs_data['stampMetadata']
            elif 'cryptographic_stamp' in firs_data:
                self.firs_stamp_metadata = firs_data['cryptographic_stamp']
            self.firs_received_at = datetime.utcnow()
        
        # Update timestamps
        now = datetime.utcnow()
        if new_status == SubmissionStatus.SUBMITTED:
            self.submitted_at = now
        elif new_status == SubmissionStatus.ACCEPTED:
            self.accepted_at = now
        elif new_status in [SubmissionStatus.REJECTED, SubmissionStatus.FAILED]:
            self.rejected_at = now
    
    def increment_retry(self):
        """Increment retry count and update timestamp."""
        self.retry_count += 1
        self.last_retry_at = datetime.utcnow()
