"""
SI-APP Correlation Model
========================
Model for tracking correlation between SI-generated invoices and APP FIRS submissions.
This enables status synchronization between SI and APP roles.
"""

import uuid
import enum
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, String, ForeignKey, Boolean, Text, JSON, Enum, DateTime, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import BaseModel

class CorrelationStatus(enum.Enum):
    """Status of SI-APP correlation."""
    
    SI_GENERATED = "si_generated"           # SI has generated the invoice
    APP_RECEIVED = "app_received"           # APP has received the invoice for submission  
    APP_SUBMITTING = "app_submitting"       # APP is submitting to FIRS
    APP_SUBMITTED = "app_submitted"         # APP has submitted to FIRS
    FIRS_ACCEPTED = "firs_accepted"         # FIRS has accepted the submission
    FIRS_REJECTED = "firs_rejected"         # FIRS has rejected the submission
    FAILED = "failed"                       # Submission failed
    CANCELLED = "cancelled"                 # Submission cancelled

class SIAPPCorrelation(BaseModel):
    """
    Model for tracking correlation between SI invoice generation and APP FIRS submission.
    
    This enables:
    - Status tracking from SI to APP
    - Bidirectional status synchronization
    - Audit trail of submission lifecycle
    """
    
    __tablename__ = "si_app_correlations"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    correlation_id = Column(String(100), nullable=False, unique=True, index=True)  # Unique correlation identifier
    
    # Organization context
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # SI-side information
    si_invoice_id = Column(String(100), nullable=False, index=True)  # SI-generated invoice identifier
    si_transaction_ids = Column(JSON, nullable=False)  # List of transaction IDs from SI
    irn = Column(String(100), nullable=False, index=True)  # Generated IRN
    si_generated_at = Column(DateTime(timezone=True), nullable=False)
    
    # APP-side information
    app_submission_id = Column(String(100), nullable=True, index=True)  # APP submission identifier
    app_received_at = Column(DateTime(timezone=True), nullable=True)
    app_submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # FIRS response information
    firs_response_id = Column(String(100), nullable=True)  # FIRS response identifier
    firs_status = Column(String(50), nullable=True)  # FIRS status response
    firs_response_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking
    current_status = Column(Enum(CorrelationStatus), nullable=False, default=CorrelationStatus.SI_GENERATED, index=True)
    last_status_update = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Invoice details
    invoice_number = Column(String(100), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), nullable=False, default='NGN')
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=True)
    customer_tin = Column(String(50), nullable=True)
    
    # Metadata and context
    invoice_data = Column(JSON, nullable=True)  # Full invoice data from SI
    submission_metadata = Column(JSON, nullable=True)  # APP submission metadata
    firs_response_data = Column(JSON, nullable=True)  # FIRS response data
    error_details = Column(JSON, nullable=True)  # Error details if any
    
    # Status history (for audit trail)
    status_history = Column(JSON, nullable=True)  # Array of status change events
    
    # Retry and recovery
    retry_count = Column(String(10), nullable=False, default='0')
    max_retries = Column(String(10), nullable=False, default='3')
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="si_app_correlations")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.correlation_id:
            self.correlation_id = f"COR-{uuid.uuid4().hex[:12].upper()}"
        if not self.status_history:
            self.status_history = []
    
    def update_status(self, new_status: CorrelationStatus, metadata: dict = None):
        """Update correlation status and add to history."""
        old_status = self.current_status
        self.current_status = new_status
        self.last_status_update = datetime.utcnow()
        
        # Add to status history
        history_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'from_status': old_status.value if old_status else None,
            'to_status': new_status.value,
            'metadata': metadata or {}
        }
        
        if not self.status_history:
            self.status_history = []
        self.status_history.append(history_entry)
    
    def set_app_received(self, app_submission_id: str, metadata: dict = None):
        """Mark as received by APP."""
        self.app_submission_id = app_submission_id
        self.app_received_at = datetime.utcnow()
        self.update_status(CorrelationStatus.APP_RECEIVED, metadata)
    
    def set_app_submitting(self, metadata: dict = None):
        """Mark as being submitted by APP."""
        self.update_status(CorrelationStatus.APP_SUBMITTING, metadata)
    
    def set_app_submitted(self, metadata: dict = None):
        """Mark as submitted by APP."""
        self.app_submitted_at = datetime.utcnow()
        self.update_status(CorrelationStatus.APP_SUBMITTED, metadata)
    
    def set_firs_response(
        self,
        firs_response_id: str,
        firs_status: str,
        response_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Set FIRS response information."""
        self.firs_response_id = firs_response_id
        self.firs_status = firs_status
        self.firs_response_at = datetime.utcnow()
        self.firs_response_data = response_data

        # Update status based on FIRS response
        status_metadata: Dict[str, Any] = {'firs_status': firs_status}
        if metadata:
            status_metadata.update(metadata)

        lowered_status = firs_status.lower() if isinstance(firs_status, str) else str(firs_status).lower()

        if lowered_status in ['accepted', 'success', 'approved']:
            self.update_status(CorrelationStatus.FIRS_ACCEPTED, status_metadata)
        elif lowered_status in ['rejected', 'failed', 'error']:
            self.update_status(CorrelationStatus.FIRS_REJECTED, status_metadata)
        else:
            self.update_status(self.current_status, status_metadata)
    
    def set_failed(self, error_details: dict = None):
        """Mark correlation as failed."""
        self.error_details = error_details
        self.update_status(CorrelationStatus.FAILED, {'error_details': error_details})
    
    def increment_retry(self):
        """Increment retry count."""
        self.retry_count = str(int(self.retry_count) + 1)
    
    def can_retry(self) -> bool:
        """Check if correlation can be retried."""
        return int(self.retry_count) < int(self.max_retries)
    
    @property
    def is_complete(self) -> bool:
        """Check if correlation is in a final state."""
        return self.current_status in [
            CorrelationStatus.FIRS_ACCEPTED,
            CorrelationStatus.FIRS_REJECTED,
            CorrelationStatus.FAILED,
            CorrelationStatus.CANCELLED
        ]
    
    @property
    def is_successful(self) -> bool:
        """Check if correlation completed successfully."""
        return self.current_status == CorrelationStatus.FIRS_ACCEPTED
    
    @property
    def processing_duration(self) -> int:
        """Get processing duration in seconds."""
        if self.firs_response_at and self.si_generated_at:
            return int((self.firs_response_at - self.si_generated_at).total_seconds())
        return 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            'id': str(self.id),
            'correlation_id': self.correlation_id,
            'organization_id': str(self.organization_id),
            'si_invoice_id': self.si_invoice_id,
            'app_submission_id': self.app_submission_id,
            'irn': self.irn,
            'current_status': self.current_status.value,
            'last_status_update': self.last_status_update.isoformat() if self.last_status_update else None,
            'invoice_number': self.invoice_number,
            'total_amount': float(self.total_amount),
            'currency': self.currency,
            'customer_name': self.customer_name,
            'processing_duration': self.processing_duration,
            'is_complete': self.is_complete,
            'is_successful': self.is_successful,
            'retry_count': self.retry_count,
            'firs_status': self.firs_status
        }
