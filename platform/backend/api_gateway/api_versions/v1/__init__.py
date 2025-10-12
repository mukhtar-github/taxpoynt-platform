"""
API Version 1 (v1)
=================
TaxPoynt E-Invoice Platform API Version 1 - Initial stable release.

This version provides:
- System Integrator endpoints for ERP/CRM/POS integration
- Access Point Provider endpoints for FIRS compliance
- Hybrid endpoints for cross-role functionality
- Role-based authentication and authorization
- Nigerian e-invoicing compliance features
"""

# Import all SI endpoints
try:
    from .si_endpoints import (
        create_banking_router,
        create_payment_processor_router,
        create_validation_router,
        create_organization_router,
        create_erp_router,
        create_crm_router,
        create_pos_router,
        create_transaction_router,
        create_compliance_router
    )
    SI_ENDPOINTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: SI endpoints not available in v1: {e}")
    SI_ENDPOINTS_AVAILABLE = False

__version__ = "1.0.0"
__api_version__ = "v1"
__status__ = "stable"

__all__ = [
    "__version__",
    "__api_version__",
    "__status__",
    "SI_ENDPOINTS_AVAILABLE"
]

if SI_ENDPOINTS_AVAILABLE:
    __all__.extend([
        "create_banking_router",
        "create_payment_processor_router",
        "create_validation_router",
        "create_organization_router",
        "create_erp_router",
        "create_crm_router",
        "create_pos_router",
        "create_transaction_router",
        "create_compliance_router",
            ])
