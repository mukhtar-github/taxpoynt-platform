"""
API Versions Management
======================
TaxPoynt API version management and routing for all platform endpoints.

**Available Versions:**
- v1: Initial stable release with core functionality
- v2: Enhanced version with additional features

**Version Structure:**
Each version provides role-specific endpoints:
- SI Endpoints: System Integrator functionality
- APP Endpoints: Access Point Provider functionality  
- Hybrid Endpoints: Cross-role functionality
"""

# Version 1 imports
try:
    from .v1.si_endpoints import (
        create_banking_router as v1_create_banking_router,
        create_payment_processor_router as v1_create_payment_processor_router,
        create_validation_router as v1_create_validation_router
    )
    V1_AVAILABLE = True
except ImportError:
    V1_AVAILABLE = False

# Version 2 imports
try:
    from .v2.si_endpoints import (
        create_banking_router as v2_create_banking_router,
        create_payment_processor_router as v2_create_payment_processor_router,
        create_validation_router as v2_create_validation_router
    )
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False

__all__ = [
    "V1_AVAILABLE",
    "V2_AVAILABLE"
]

# Add version-specific exports if available
if V1_AVAILABLE:
    __all__.extend([
        "v1_create_banking_router",
        "v1_create_payment_processor_router", 
        "v1_create_validation_router"
    ])

if V2_AVAILABLE:
    __all__.extend([
        "v2_create_banking_router",
        "v2_create_payment_processor_router",
        "v2_create_validation_router"
    ])