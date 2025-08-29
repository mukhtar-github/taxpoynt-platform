"""
TaxPoynt Platform - Core Database Models
======================================
SQLAlchemy models for the TaxPoynt platform, adapted from legacy architecture
with enhancements for role-based access control and multi-service support.
"""

from .base import Base
from .user import User, UserRole, UserServiceAccess
from .organization import Organization, OrganizationUser
from .integration import Integration, IntegrationCredentials
from .firs_submission import FIRSSubmission
from .banking import (
    BankingConnection, BankAccount, BankTransaction, 
    BankingWebhook, BankingSyncLog, BankingCredentials,
    BankingProvider, ConnectionStatus, TransactionType, AccountType
)
from .business_systems import (
    # ERP Models
    ERPConnection, ERPSyncLog,
    # CRM Models  
    CRMConnection, CRMSyncLog,
    # POS Models
    POSConnection, POSTransactionLog,
    # Certificate Models
    Certificate,
    # Document Models
    DocumentTemplate, DocumentGenerationLog,
    # IRN/QR Models
    IRNGeneration,
    # Taxpayer Models
    Taxpayer,
    # Webhook Models
    WebhookEvent,
    # Analytics Models
    AnalyticsReport,
    # Audit Models
    AuditLog, ComplianceCheck,
    # Enums
    IntegrationType, ERPProvider, CRMProvider, POSProvider, EcommerceProvider,
    SyncStatus, CertificateType, CertificateStatus, DocumentType,
    TaxpayerStatus, WebhookEventType, AuditEventType
)

# SDK Management Models
from .sdk_management import (
    SDK, SDKVersion, SDKDownload, SDKUsageLog, SandboxScenario, 
    SandboxTestResult, SDKDocumentation, SDKFeedback, SDKAnalytics,
    SDKLanguage, SDKStatus, FeedbackType, TestStatus,
    DEMO_SDK_DATA, DEMO_SCENARIOS
)

__all__ = [
    "Base",
    "User", 
    "UserRole",
    "UserServiceAccess",
    "Organization",
    "OrganizationUser", 
    "Integration",
    "IntegrationCredentials",
    "FIRSSubmission",
    "BankingConnection",
    "BankAccount",
    "BankTransaction",
    "BankingWebhook",
    "BankingSyncLog",
    "BankingCredentials",
    "BankingProvider",
    "ConnectionStatus",
    "TransactionType",
    "AccountType",
    # Business Systems Models
    "ERPConnection",
    "ERPSyncLog",
    "CRMConnection",
    "CRMSyncLog",
    "POSConnection",
    "POSTransactionLog",
    "Certificate",
    "DocumentTemplate",
    "DocumentGenerationLog",
    "IRNGeneration",
    "Taxpayer",
    "WebhookEvent",
    "AnalyticsReport",
    "AuditLog",
    "ComplianceCheck",
    # Enums
    "IntegrationType",
    "ERPProvider",
    "CRMProvider",
    "POSProvider",
    "EcommerceProvider",
    "SyncStatus",
    "CertificateType",
    "CertificateStatus",
    "DocumentType",
    "TaxpayerStatus",
    "WebhookEventType",
    "AuditEventType",
    # SDK Management Models
    "SDK",
    "SDKVersion", 
    "SDKDownload",
    "SDKUsageLog",
    "SandboxScenario",
    "SandboxTestResult",
    "SDKDocumentation",
    "SDKFeedback",
    "SDKAnalytics",
    "SDKLanguage",
    "SDKStatus",
    "FeedbackType",
    "TestStatus",
    "DEMO_SDK_DATA",
    "DEMO_SCENARIOS"
]