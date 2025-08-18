"""
TaxPoynt Platform - Business Systems Database Models
===================================================
SQLAlchemy models for all business system integrations, compliance tracking,
and cross-role operations in the TaxPoynt platform.

**Model Categories:**
- ERP Integration Models (Odoo, SAP, Oracle, Dynamics, NetSuite)
- CRM Integration Models (Salesforce, HubSpot, Pipedrive)
- POS Integration Models (Toast, Clover, Square, Nigerian POS)
- E-commerce Models (Shopify, WooCommerce, Magento, BigCommerce)
- Certificate Management Models (SI & APP certificates)
- Document Processing Models (Invoice generation, templates)
- IRN/QR Models (FIRS IRN generation, QR codes)
- Taxpayer Management Models (FIRS taxpayer registration)
- Webhook Processing Models (FIRS & third-party webhooks)
- Analytics & Reporting Models (Cross-role analytics)
- Audit & Compliance Models (Cross-role audit trails)
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Numeric, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid
from enum import Enum as PyEnum


# ==============================================================================
# ENUMS
# ==============================================================================

class IntegrationType(str, PyEnum):
    """Types of business system integrations"""
    ERP = "erp"
    CRM = "crm" 
    POS = "pos"
    ECOMMERCE = "ecommerce"
    BANKING = "banking"
    ACCOUNTING = "accounting"
    INVENTORY = "inventory"
    PAYMENT_PROCESSOR = "payment_processor"


class ERPProvider(str, PyEnum):
    """ERP system providers"""
    ODOO = "odoo"
    SAP = "sap"
    ORACLE = "oracle"
    DYNAMICS = "dynamics"
    NETSUITE = "netsuite"
    QUICKBOOKS = "quickbooks"
    SAGE = "sage"


class CRMProvider(str, PyEnum):
    """CRM system providers"""
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"
    FRESHWORKS = "freshworks"


class POSProvider(str, PyEnum):
    """POS system providers"""
    TOAST = "toast"
    CLOVER = "clover"
    SQUARE = "square"
    MONIEPOINT = "moniepoint"
    OPAY = "opay"
    PALMPAY = "palmpay"


class EcommerceProvider(str, PyEnum):
    """E-commerce platform providers"""
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"
    BIGCOMMERCE = "bigcommerce"
    JUMIA = "jumia"


class SyncStatus(str, PyEnum):
    """Data synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


class CertificateType(str, PyEnum):
    """Certificate types"""
    FIRS_DIGITAL_CERTIFICATE = "firs_digital_certificate"
    SSL_TLS_CERTIFICATE = "ssl_tls_certificate"
    API_CERTIFICATE = "api_certificate"
    SIGNING_CERTIFICATE = "signing_certificate"


class CertificateStatus(str, PyEnum):
    """Certificate status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING_RENEWAL = "pending_renewal"
    SUSPENDED = "suspended"


class DocumentType(str, PyEnum):
    """Document types for processing"""
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    RECEIPT = "receipt"
    PROFORMA = "proforma"
    QUOTE = "quote"


class TaxpayerStatus(str, PyEnum):
    """FIRS taxpayer status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_REGISTRATION = "pending_registration"
    CANCELLED = "cancelled"


class WebhookEventType(str, PyEnum):
    """Webhook event types"""
    FIRS_SUBMISSION_STATUS = "firs_submission_status"
    FIRS_VALIDATION_RESULT = "firs_validation_result"
    BANKING_TRANSACTION = "banking_transaction"
    ERP_DATA_CHANGE = "erp_data_change"
    POS_TRANSACTION = "pos_transaction"


class AuditEventType(str, PyEnum):
    """Audit event types"""
    USER_LOGIN = "user_login"
    DATA_ACCESS = "data_access"
    SYSTEM_CONFIGURATION = "system_configuration"
    INTEGRATION_CHANGE = "integration_change"
    COMPLIANCE_CHECK = "compliance_check"
    DATA_EXPORT = "data_export"


# ==============================================================================
# ERP INTEGRATION MODELS
# ==============================================================================

class ERPConnection(BaseModel):
    """ERP system connections and configurations"""
    __tablename__ = "erp_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    si_id = Column(UUID(as_uuid=True), nullable=False)  # System Integrator ID
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # ERP system details
    provider = Column(Enum(ERPProvider), nullable=False)
    system_name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=True)
    base_url = Column(String(500), nullable=True)
    
    # Connection status
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    next_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    sync_frequency_hours = Column(Integer, default=24)
    sync_configuration = Column(JSONB, default={})
    
    # Authentication reference
    credentials_id = Column(UUID(as_uuid=True), ForeignKey("integration_credentials.id"), nullable=True)
    
    # Relationships
    sync_logs = relationship("ERPSyncLog", back_populates="connection", cascade="all, delete-orphan")


class ERPSyncLog(BaseModel):
    """ERP data synchronization logs"""
    __tablename__ = "erp_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("erp_connections.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # customers, products, invoices, etc.
    status = Column(Enum(SyncStatus), nullable=False)
    
    # Statistics
    records_fetched = Column(Integer, default=0)
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, default={})
    
    # Sync metadata
    sync_metadata = Column(JSONB, default={})
    
    # Relationships
    connection = relationship("ERPConnection", back_populates="sync_logs")


# ==============================================================================
# CRM INTEGRATION MODELS
# ==============================================================================

class CRMConnection(BaseModel):
    """CRM system connections and configurations"""
    __tablename__ = "crm_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    si_id = Column(UUID(as_uuid=True), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # CRM system details
    provider = Column(Enum(CRMProvider), nullable=False)
    system_name = Column(String(255), nullable=False)
    instance_url = Column(String(500), nullable=True)
    
    # Connection status
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    is_active = Column(Boolean, default=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    sync_configuration = Column(JSONB, default={})
    
    # Authentication reference
    credentials_id = Column(UUID(as_uuid=True), ForeignKey("integration_credentials.id"), nullable=True)
    
    # Relationships
    sync_logs = relationship("CRMSyncLog", back_populates="connection", cascade="all, delete-orphan")


class CRMSyncLog(BaseModel):
    """CRM data synchronization logs"""
    __tablename__ = "crm_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("crm_connections.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # contacts, leads, opportunities, etc.
    status = Column(Enum(SyncStatus), nullable=False)
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Relationships
    connection = relationship("CRMConnection", back_populates="sync_logs")


# ==============================================================================
# POS INTEGRATION MODELS
# ==============================================================================

class POSConnection(BaseModel):
    """POS system connections and device management"""
    __tablename__ = "pos_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    si_id = Column(UUID(as_uuid=True), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # POS system details
    provider = Column(Enum(POSProvider), nullable=False)
    device_name = Column(String(255), nullable=False)
    device_id = Column(String(255), nullable=True)
    location_name = Column(String(255), nullable=True)
    
    # Connection status
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    is_active = Column(Boolean, default=True)
    last_transaction_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    sync_configuration = Column(JSONB, default={})
    
    # Authentication reference
    credentials_id = Column(UUID(as_uuid=True), ForeignKey("integration_credentials.id"), nullable=True)
    
    # Relationships
    transaction_logs = relationship("POSTransactionLog", back_populates="connection", cascade="all, delete-orphan")


class POSTransactionLog(BaseModel):
    """POS transaction synchronization logs"""
    __tablename__ = "pos_transaction_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("pos_connections.id"), nullable=False)
    
    # Transaction details
    pos_transaction_id = Column(String(255), nullable=False)
    transaction_amount = Column(Numeric(15, 2), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=True)
    
    # Sync status
    sync_status = Column(Enum(SyncStatus), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Invoice generation
    invoice_generated = Column(Boolean, default=False)
    invoice_reference = Column(String(255), nullable=True)
    
    # Metadata
    transaction_metadata = Column(JSONB, default={})
    
    # Relationships
    connection = relationship("POSConnection", back_populates="transaction_logs")


# ==============================================================================
# CERTIFICATE MANAGEMENT MODELS
# ==============================================================================

class Certificate(BaseModel):
    """Digital certificates for SI and APP operations"""
    __tablename__ = "certificates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Certificate details
    certificate_type = Column(Enum(CertificateType), nullable=False)
    certificate_name = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=True)
    
    # Certificate content (encrypted)
    certificate_data = Column(Text, nullable=True)  # Base64 encoded certificate
    private_key_data = Column(Text, nullable=True)  # Encrypted private key
    
    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(CertificateStatus), default=CertificateStatus.ACTIVE)
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Certificate metadata
    certificate_metadata = Column(JSONB, default={})


# ==============================================================================
# DOCUMENT PROCESSING MODELS
# ==============================================================================

class DocumentTemplate(BaseModel):
    """Invoice and document templates"""
    __tablename__ = "document_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Template details
    template_name = Column(String(255), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    template_version = Column(String(50), default="1.0")
    
    # Template content
    template_data = Column(JSONB, nullable=False)  # Template structure
    style_configuration = Column(JSONB, default={})  # Styling rules
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)


class DocumentGenerationLog(BaseModel):
    """Document generation history and tracking"""
    __tablename__ = "document_generation_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("document_templates.id"), nullable=True)
    
    # Document details
    document_type = Column(Enum(DocumentType), nullable=False)
    document_reference = Column(String(255), nullable=False)
    
    # Generation status
    generation_status = Column(Enum(SyncStatus), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # File information
    file_size_bytes = Column(Integer, nullable=True)
    file_format = Column(String(10), nullable=True)  # PDF, XML, etc.
    storage_path = Column(String(500), nullable=True)
    
    # Processing metadata
    generation_metadata = Column(JSONB, default={})
    error_details = Column(Text, nullable=True)


# ==============================================================================
# IRN/QR GENERATION MODELS
# ==============================================================================

class IRNGeneration(BaseModel):
    """FIRS IRN generation tracking"""
    __tablename__ = "irn_generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # IRN details
    irn_number = Column(String(255), nullable=False, unique=True)
    invoice_reference = Column(String(255), nullable=False)
    invoice_hash = Column(String(255), nullable=True)
    
    # QR code
    qr_code_data = Column(Text, nullable=True)  # Base64 encoded QR code
    qr_code_metadata = Column(JSONB, default={})
    
    # Generation status
    generation_status = Column(Enum(SyncStatus), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # FIRS submission
    submitted_to_firs = Column(Boolean, default=False)
    firs_submission_id = Column(UUID(as_uuid=True), ForeignKey("firs_submissions.id"), nullable=True)
    
    # Validation
    validation_status = Column(String(50), nullable=True)
    validation_details = Column(JSONB, default={})


# ==============================================================================
# TAXPAYER MANAGEMENT MODELS
# ==============================================================================

class Taxpayer(BaseModel):
    """FIRS taxpayer registration and management"""
    __tablename__ = "taxpayers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Taxpayer identification
    tin = Column(String(50), nullable=False, unique=True)
    business_name = Column(String(255), nullable=False)
    registration_number = Column(String(100), nullable=True)
    
    # FIRS registration details
    firs_taxpayer_id = Column(String(255), nullable=True)
    registration_status = Column(Enum(TaxpayerStatus), default=TaxpayerStatus.PENDING_REGISTRATION)
    registration_date = Column(DateTime(timezone=True), nullable=True)
    
    # Business information
    business_type = Column(String(100), nullable=True)
    sector = Column(String(100), nullable=True)
    business_address = Column(Text, nullable=True)
    
    # Contact information
    contact_person = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Compliance status
    vat_registered = Column(Boolean, default=False)
    vat_number = Column(String(50), nullable=True)
    compliance_level = Column(String(50), nullable=True)
    
    # Metadata
    taxpayer_metadata = Column(JSONB, default={})
    last_updated_from_firs = Column(DateTime(timezone=True), nullable=True)


# ==============================================================================
# WEBHOOK PROCESSING MODELS
# ==============================================================================

class WebhookEvent(BaseModel):
    """Webhook events from FIRS and third-party systems"""
    __tablename__ = "webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Webhook source
    source_system = Column(String(100), nullable=False)  # FIRS, Mono, etc.
    event_type = Column(Enum(WebhookEventType), nullable=False)
    webhook_id = Column(String(255), nullable=True)  # External webhook ID
    
    # Event data
    event_data = Column(JSONB, nullable=False)
    raw_payload = Column(Text, nullable=True)
    headers = Column(JSONB, default={})
    
    # Processing status
    processing_status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, default={})
    
    # Security
    signature_valid = Column(Boolean, nullable=True)
    source_ip = Column(String(45), nullable=True)


# ==============================================================================
# ANALYTICS & REPORTING MODELS
# ==============================================================================

class AnalyticsReport(BaseModel):
    """Generated analytics reports"""
    __tablename__ = "analytics_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Report details
    report_name = Column(String(255), nullable=False)
    report_type = Column(String(100), nullable=False)  # dashboard, compliance, usage, etc.
    report_period = Column(String(50), nullable=True)  # daily, weekly, monthly
    
    # Report data
    report_data = Column(JSONB, nullable=False)
    summary_metrics = Column(JSONB, default={})
    
    # Generation details
    generated_by = Column(UUID(as_uuid=True), nullable=True)  # User ID
    generation_status = Column(Enum(SyncStatus), nullable=False)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Access control
    is_public = Column(Boolean, default=False)
    access_roles = Column(JSONB, default=[])  # Roles that can access
    
    # File storage
    file_path = Column(String(500), nullable=True)
    file_format = Column(String(10), nullable=True)


# ==============================================================================
# AUDIT & COMPLIANCE MODELS
# ==============================================================================

class AuditLog(BaseModel):
    """System-wide audit trail"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    event_type = Column(Enum(AuditEventType), nullable=False)
    event_description = Column(String(500), nullable=False)
    
    # Actor information
    user_id = Column(UUID(as_uuid=True), nullable=True)
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Target information
    target_type = Column(String(100), nullable=True)  # user, organization, integration
    target_id = Column(String(255), nullable=True)
    
    # Event data
    event_data = Column(JSONB, default={})
    old_values = Column(JSONB, default={})
    new_values = Column(JSONB, default={})
    
    # Context
    session_id = Column(String(255), nullable=True)
    correlation_id = Column(String(255), nullable=True)
    
    # Compliance
    compliance_relevant = Column(Boolean, default=False)
    retention_until = Column(DateTime(timezone=True), nullable=True)


class ComplianceCheck(BaseModel):
    """Compliance validation results"""
    __tablename__ = "compliance_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Check details
    check_type = Column(String(100), nullable=False)  # FIRS, GDPR, NITDA, etc.
    check_name = Column(String(255), nullable=False)
    check_version = Column(String(50), nullable=True)
    
    # Results
    compliance_status = Column(String(50), nullable=False)  # compliant, non_compliant, warning
    score = Column(Numeric(5, 2), nullable=True)  # Compliance score 0-100
    
    # Check data
    check_results = Column(JSONB, nullable=False)
    recommendations = Column(JSONB, default=[])
    
    # Execution details
    checked_at = Column(DateTime(timezone=True), nullable=False)
    checked_by = Column(UUID(as_uuid=True), nullable=True)  # User or system ID
    
    # Follow-up
    next_check_due = Column(DateTime(timezone=True), nullable=True)
    remediation_deadline = Column(DateTime(timezone=True), nullable=True)
    remediation_status = Column(String(50), nullable=True)