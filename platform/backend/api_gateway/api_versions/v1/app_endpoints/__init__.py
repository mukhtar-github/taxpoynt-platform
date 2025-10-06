"""
Access Point Provider (APP) Endpoints - API Version 1
=====================================================
Version 1 of APP role endpoints for FIRS e-invoicing compliance and taxpayer management.

**APP Role Context:**
TaxPoynt serves as an Access Point Provider (APP) for FIRS e-invoicing compliance.
APP endpoints handle direct integration with FIRS systems and taxpayer management.

**Professional Structure:**
- FIRS Integration: Direct communication with FIRS e-invoicing systems
- Taxpayer Management: Onboard and manage taxpayers for e-invoicing compliance
- Invoice Submission: Submit compliant invoices to FIRS on behalf of taxpayers
- Compliance Validation: Validate invoices against FIRS requirements
- Certificate Management: Handle FIRS certificates and authentication
- Grant Management: Track FIRS grant milestones and performance metrics
- Security Management: Security monitoring, threat detection, and compliance scanning
- Validation Management: Invoice validation, data quality checks, and pre-transmission validation
- Transmission Management: FIRS transmission, batch processing, and status tracking
- Tracking Management: Real-time tracking and monitoring of transmission status
- Report Generation: Custom compliance and transmission reports
"""

from .firs_integration_endpoints import create_firs_integration_router
from .taxpayer_management_endpoints import create_taxpayer_management_router
from .invoice_submission_endpoints import create_invoice_submission_router
from .compliance_validation_endpoints import create_compliance_validation_router
from .certificate_management_endpoints import create_certificate_management_router
from .grant_management_endpoints import create_grant_management_router
from .security_management_endpoints import create_security_management_router
from .validation_management_endpoints import create_validation_management_router
from .transmission_management_endpoints import create_transmission_management_router
from .tracking_management_endpoints import create_tracking_management_router
from .report_generation_endpoints import create_report_generation_router
from .dashboard_data_endpoints import create_dashboard_data_router
from .setup_endpoints import create_app_setup_router
from .webhook_endpoints import create_app_webhook_router
from .main_router import create_app_v1_router

__all__ = [
    "create_firs_integration_router",
    "create_taxpayer_management_router",
    "create_invoice_submission_router",
    "create_compliance_validation_router",
    "create_certificate_management_router",
    "create_grant_management_router",
    "create_security_management_router",
    "create_validation_management_router",
    "create_transmission_management_router",
    "create_tracking_management_router",
    "create_report_generation_router",
    "create_dashboard_data_router",
    "create_app_setup_router",
    "create_app_webhook_router",
    "create_app_v1_router"
]
