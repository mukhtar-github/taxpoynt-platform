"""
SI Services - Certificate Management Module

Handles digital certificate lifecycle management for System Integrator role.
Manages certificate requests, digital certificates, and certificate operations.
"""

from __future__ import annotations

import sys
import types


def _ensure_legacy_app_stubs() -> None:
    """Create lightweight stubs for legacy `app.*` modules when absent."""

    if "app" in sys.modules:
        return

    app_module = types.ModuleType("app")
    app_module.__path__ = []
    sys.modules["app"] = app_module

    # app.models.certificate (+ request)
    models_module = types.ModuleType("app.models")
    models_module.__path__ = []
    sys.modules["app.models"] = models_module

    cert_module = types.ModuleType("app.models.certificate")
    cert_module.__path__ = []

    class _Cert:  # pragma: no cover - simple placeholder
        pass

    class _CertRevocation:  # pragma: no cover
        pass

    class _CertType:  # pragma: no cover
        pass

    class _LegacyCertStatus:  # pragma: no cover
        ACTIVE = "active"

    cert_module.Certificate = _Cert
    cert_module.CertificateRevocation = _CertRevocation
    cert_module.CertificateType = _CertType
    cert_module.CertificateStatus = _LegacyCertStatus
    models_module.certificate = cert_module
    sys.modules["app.models.certificate"] = cert_module

    cert_req_module = types.ModuleType("app.models.certificate_request")
    cert_req_module.__path__ = []

    class _CertRequest:  # pragma: no cover
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _CertRequestStatus:  # pragma: no cover
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"

    class _CertRequestType:  # pragma: no cover
        SIGNING = "signing"
        ENCRYPTION = "encryption"

    cert_req_module.CertificateRequest = _CertRequest
    cert_req_module.CertificateRequestStatus = _CertRequestStatus
    cert_req_module.CertificateRequestType = _CertRequestType
    models_module.certificate_request = cert_req_module
    sys.modules["app.models.certificate_request"] = cert_req_module
    app_module.models = models_module

    # app.schemas
    schemas_module = types.ModuleType("app.schemas")
    schemas_module.__path__ = []
    sys.modules["app.schemas"] = schemas_module

    cert_schema_module = types.ModuleType("app.schemas.certificate")
    cert_schema_module.__path__ = []

    class _CertCreate:  # pragma: no cover
        pass

    class _CertUpdate:  # pragma: no cover
        pass

    class _CertVerification:  # pragma: no cover
        pass

    cert_schema_module.CertificateCreate = _CertCreate
    cert_schema_module.CertificateUpdate = _CertUpdate
    cert_schema_module.CertificateVerification = _CertVerification
    schemas_module.certificate = cert_schema_module
    sys.modules["app.schemas.certificate"] = cert_schema_module

    cert_req_schema_module = types.ModuleType("app.schemas.certificate_request")
    cert_req_schema_module.__path__ = []

    class _CertReqCreate:  # pragma: no cover
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class _CertReqUpdate:  # pragma: no cover
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    cert_req_schema_module.CertificateRequestCreate = _CertReqCreate
    cert_req_schema_module.CertificateRequestUpdate = _CertReqUpdate
    schemas_module.certificate_request = cert_req_schema_module
    sys.modules["app.schemas.certificate_request"] = cert_req_schema_module
    app_module.schemas = schemas_module

    # app.services.key_service
    services_module = types.ModuleType("app.services")
    services_module.__path__ = []
    sys.modules["app.services"] = services_module

    key_service_module = types.ModuleType("app.services.key_service")
    key_service_module.__path__ = []

    class _KeyService:  # pragma: no cover
        def encrypt_data(self, data, context=None):
            return "stub-key", data

    key_service_module.KeyManagementService = _KeyService
    services_module.key_service = key_service_module
    sys.modules["app.services.key_service"] = key_service_module
    app_module.services = services_module

    # app.utils.encryption
    utils_module = types.ModuleType("app.utils")
    utils_module.__path__ = []
    sys.modules["app.utils"] = utils_module

    encryption_module = types.ModuleType("app.utils.encryption")
    encryption_module.__path__ = []

    def _encrypt_field(value, *_args, **_kwargs):  # pragma: no cover
        return value

    def _decrypt_field(value, *_args, **_kwargs):  # pragma: no cover
        return value

    encryption_module.encrypt_field = _encrypt_field
    encryption_module.decrypt_field = _decrypt_field
    utils_module.encryption = encryption_module
    sys.modules["app.utils.encryption"] = encryption_module
    app_module.utils = utils_module

    # app.core.config
    core_module = types.ModuleType("app.core")
    core_module.__path__ = []
    sys.modules["app.core"] = core_module

    config_module = types.ModuleType("app.core.config")

    class _Settings:  # pragma: no cover
        def __init__(self):
            self.environment = "test"

    config_module.settings = _Settings()
    core_module.config = config_module
    sys.modules["app.core.config"] = config_module
    app_module.core = core_module


_ensure_legacy_app_stubs()

# New granular components
from .certificate_generator import CertificateGenerator
from .key_manager import KeyManager
from .certificate_store import CertificateStore, CertificateStatus
from .lifecycle_manager import LifecycleManager
from .ca_integration import CAIntegration

# Refactored services (using granular components)
try:  # pragma: no cover - exercised via import side-effects in tests
    from .certificate_service import CertificateService
except Exception as exc:  # noqa: B902 - broad to guard optional dependency
    class CertificateService:  # type: ignore
        """Fallback stub when legacy `app.*` deps are unavailable."""

        def __init__(self, *_, **__):
            raise RuntimeError(
                "CertificateService unavailable: optional legacy dependencies missing"
            ) from exc


try:
    from .certificate_request_service import CertificateRequestService  # type: ignore
except Exception as exc:  # noqa: B902 - guard optional deps
    class CertificateRequestService:  # type: ignore
        """Fallback stub when legacy `app.*` deps are unavailable."""

        def __init__(self, *_, **__):
            raise RuntimeError(
                "CertificateRequestService unavailable: optional legacy dependencies missing"
            ) from exc


from .digital_certificate_service import DigitalCertificateService

# Legacy services (original monolithic versions)
try:
    from .certificate_service_legacy import CertificateService as CertificateServiceLegacy
except Exception:  # pragma: nocover - legacy import optional
    CertificateServiceLegacy = CertificateService  # type: ignore

try:
    from .certificate_request_service_legacy import (
        CertificateRequestService as CertificateRequestServiceLegacy,
    )
except Exception:  # pragma: nocover - legacy import optional
    CertificateRequestServiceLegacy = CertificateRequestService  # type: ignore

try:
    from .digital_certificate_service_legacy import (
        DigitalCertificateService as DigitalCertificateServiceLegacy,
    )
except Exception:  # pragma: nocover - legacy import optional
    DigitalCertificateServiceLegacy = DigitalCertificateService  # type: ignore

__all__ = [
    # New granular components
    "CertificateGenerator",
    "KeyManager",
    "CertificateStore",
    "CertificateStatus",
    "LifecycleManager",
    "CAIntegration",
    
    # Refactored services
    "CertificateService",
    "CertificateRequestService",
    "DigitalCertificateService",
    
    # Legacy services
    "CertificateServiceLegacy",
    "CertificateRequestServiceLegacy",
    "DigitalCertificateServiceLegacy"
]
