"""
APP Setup Endpoints - API v1
============================
Handles Access Point Provider setup flows that persist configuration data
collected during guided onboarding (e.g. FIRS invoice processing wizard).
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field, ValidationError, validator

from core_platform.authentication.role_manager import PlatformRole
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.organization import Organization
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.utils.error_mapping import v1_error_response
from api_gateway.utils.v1_response import build_v1_response
from ..version_models import V1ResponseModel
from .firs_integration_endpoints import FIRSIntegrationEndpointsV1

logger = logging.getLogger(__name__)


class FIRSConfigurationSetupRequest(BaseModel):
    """Payload collected from the APP onboarding wizard."""

    firs_api_key: str = Field(..., min_length=1, max_length=512)
    firs_api_secret: str = Field(..., min_length=1, max_length=512)
    environment: str = Field("sandbox")
    auto_validate: bool = True
    batch_processing: bool = True
    real_time_sync: bool = False
    vat_number: Optional[str] = Field(None, max_length=64)
    default_tax_rate: float = Field(7.5, ge=0, le=100)
    webhook_url: Optional[str] = Field(None, max_length=512)
    certificate_path: Optional[str] = Field(None, max_length=512)

    @validator("environment")
    def _validate_environment(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"sandbox", "production"}:
            raise ValueError("environment must be either 'sandbox' or 'production'")
        return normalized


class ComplianceSLAUpdateRequest(BaseModel):
    """Payload for adjusting compliance SLA thresholds."""

    sla_hours: int = Field(..., ge=1, le=168)


class APPSetupEndpointsV1:
    """APP setup endpoints used by onboarding experiences."""

    ACTION_NAME = "app_firs_configuration_saved"
    ACTION_READ = "app_firs_configuration_retrieved"
    ACTION_SLA_READ = "app_compliance_sla_retrieved"
    ACTION_SLA_UPDATED = "app_compliance_sla_updated"

    def __init__(
        self,
        role_detector: HTTPRoleDetector,
        permission_guard: APIPermissionGuard,
    ):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.router = APIRouter(
            prefix="/setup",
            tags=["APP Setup V1"],
            dependencies=[Depends(self._require_app_role)],
        )

        self._setup_routes()
        logger.info("APP Setup Endpoints V1 initialized")

    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        context = await self.role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Point Provider role required for v1 API",
            )
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/app{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for APP v1 endpoint",
            )
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "app"
        return context

    def _setup_routes(self) -> None:
        self.router.add_api_route(
            "/firs-configuration",
            self.get_firs_configuration,
            methods=["GET"],
            summary="Retrieve stored FIRS configuration",
            description="Return the stored FIRS configuration snapshot and connection status for the APP organization",
            response_model=V1ResponseModel,
        )

        self.router.add_api_route(
            "/firs-configuration",
            self.save_firs_configuration,
            methods=["POST"],
            summary="Persist APP FIRS configuration",
            description="Store the APP organization's FIRS credentials and processing preferences captured during onboarding",
            response_model=V1ResponseModel,
        )

        self.router.add_api_route(
            "/compliance-sla",
            self.get_compliance_sla,
            methods=["GET"],
            summary="Get compliance SLA configuration",
            description="Return the configured compliance SLA threshold for the tenant",
            response_model=V1ResponseModel,
        )

        self.router.add_api_route(
            "/compliance-sla",
            self.update_compliance_sla,
            methods=["PATCH"],
            summary="Update compliance SLA configuration",
            description="Adjust the compliance SLA threshold for the tenant",
            response_model=V1ResponseModel,
        )

    async def save_firs_configuration(self, request: Request):
        """Persist configuration provided by the APP invoice processing wizard."""

        try:
            context = await self._require_app_role(request)

            try:
                raw_body = await request.json()
            except Exception as exc:
                logger.error("Invalid JSON payload for FIRS configuration: %s", exc)
                return v1_error_response(ValueError("Invalid JSON payload"), action=self.ACTION_NAME)

            try:
                payload = FIRSConfigurationSetupRequest(**raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action=self.ACTION_NAME)

            org_id = getattr(context, "organization_id", None)
            if not org_id:
                return v1_error_response(
                    ValueError("Organization context is required"), action=self.ACTION_NAME
                )

            async for session in get_async_session():
                organization: Optional[Organization] = await session.get(Organization, org_id)
                if not organization:
                    return v1_error_response(
                        ValueError("Organization not found"), action=self.ACTION_NAME
                    )

                existing_config = dict(organization.firs_configuration or {})
                updated_config = dict(existing_config)

                updated_config["api_key"] = self._resolve_sensitive_update(
                    payload.firs_api_key, existing_config.get("api_key")
                )
                updated_config["api_secret"] = self._resolve_sensitive_update(
                    payload.firs_api_secret, existing_config.get("api_secret")
                )
                updated_config["environment"] = payload.environment
                updated_config["auto_validate"] = payload.auto_validate
                updated_config["batch_processing"] = payload.batch_processing
                updated_config["real_time_sync"] = payload.real_time_sync
                updated_config["vat_number"] = payload.vat_number
                updated_config["default_tax_rate"] = float(payload.default_tax_rate)
                updated_config["webhook_url"] = payload.webhook_url
                updated_config["certificate_path"] = payload.certificate_path

                if updated_config.get("api_key") and updated_config.get("api_secret"):
                    updated_config["connection_status"] = "configured"
                else:
                    updated_config["connection_status"] = "disconnected"

                updated_config["api_version"] = "v1"
                updated_config["last_updated_at"] = (
                    datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
                )
                updated_config["last_updated_by"] = (
                    str(context.user_id)
                    if getattr(context, "user_id", None) is not None
                    else existing_config.get("last_updated_by")
                )

                organization.firs_configuration = updated_config
                session.add(organization)
                await session.commit()
                await session.refresh(organization)

                status_payload = FIRSIntegrationEndpointsV1._build_status_payload(
                    updated_config, str(org_id)
                )
                safe_config = self._build_safe_configuration_snapshot(updated_config)

                response_payload = {
                    "status": status_payload,
                    "configuration": safe_config,
                }

                return self._create_v1_response(response_payload, self.ACTION_NAME)

            raise RuntimeError("Database session unavailable")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error saving APP FIRS configuration in v1: %s", exc, exc_info=True)
            return v1_error_response(exc, action=self.ACTION_NAME)

    async def get_firs_configuration(self, request: Request):
        """Fetch the stored FIRS configuration in a sanitized format."""

        try:
            context = await self._require_app_role(request)
            org_id = getattr(context, "organization_id", None)

            if not org_id:
                empty_payload = {
                    "configuration": None,
                    "status": FIRSIntegrationEndpointsV1._build_status_payload({}, None),
                }
                return self._create_v1_response(empty_payload, self.ACTION_READ)

            async for session in get_async_session():
                organization: Optional[Organization] = await session.get(Organization, org_id)
                if not organization:
                    payload = {
                        "configuration": None,
                        "status": FIRSIntegrationEndpointsV1._build_status_payload({}, str(org_id)),
                    }
                    payload["status"]["metadata"]["last_error"] = "organization_not_found"
                    return self._create_v1_response(payload, self.ACTION_READ)

                existing_config = dict(organization.firs_configuration or {})
                safe_config = self._build_safe_configuration_snapshot(existing_config)
                status_payload = FIRSIntegrationEndpointsV1._build_status_payload(existing_config, str(org_id))

                response_payload = {
                    "configuration": safe_config,
                    "status": status_payload,
                }

                return self._create_v1_response(response_payload, self.ACTION_READ)

            raise RuntimeError("Database session unavailable")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Failed to retrieve APP FIRS configuration: %s", exc, exc_info=True)
            return v1_error_response(exc, action=self.ACTION_READ)

    async def get_compliance_sla(self, request: Request):
        """Expose the current compliance SLA threshold."""

        try:
            context = await self._require_app_role(request)
            org_id = getattr(context, "organization_id", None)
            if not org_id:
                return v1_error_response(
                    ValueError("Organization context is required"),
                    action=self.ACTION_SLA_READ,
                )

            async for session in get_async_session():
                organization = await session.get(Organization, org_id)
                if not organization:
                    return v1_error_response(
                        ValueError("Organization not found"),
                        action=self.ACTION_SLA_READ,
                    )

                config = organization.firs_configuration or {}
                sla_hours = 4
                configured = config.get("compliance_sla_hours") if isinstance(config, dict) else None
                try:
                    if configured is not None:
                        sla_hours = max(1, int(configured))
                except (TypeError, ValueError):
                    logger.debug(
                        "Invalid compliance_sla_hours configuration for org %s", org_id
                    )

                payload = {
                    "slaHours": sla_hours,
                    "updatedAt": config.get("sla_updated_at") if isinstance(config, dict) else None,
                    "updatedBy": config.get("sla_updated_by") if isinstance(config, dict) else None,
                }

                return self._create_v1_response(payload, self.ACTION_SLA_READ)

            raise RuntimeError("Database session unavailable")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error retrieving compliance SLA configuration: %s", exc, exc_info=True)
            return v1_error_response(exc, action=self.ACTION_SLA_READ)

    async def update_compliance_sla(self, request: Request):
        """Update the compliance SLA threshold for the tenant."""

        try:
            context = await self._require_app_role(request)
            org_id = getattr(context, "organization_id", None)
            if not org_id:
                return v1_error_response(
                    ValueError("Organization context is required"),
                    action=self.ACTION_SLA_UPDATED,
                )

            try:
                raw_payload = await request.json()
            except Exception as exc:
                logger.error("Invalid JSON payload for SLA update: %s", exc)
                return v1_error_response(ValueError("Invalid JSON payload"), action=self.ACTION_SLA_UPDATED)

            try:
                payload = ComplianceSLAUpdateRequest(**raw_payload)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action=self.ACTION_SLA_UPDATED)

            async for session in get_async_session():
                organization = await session.get(Organization, org_id)
                if not organization:
                    return v1_error_response(
                        ValueError("Organization not found"),
                        action=self.ACTION_SLA_UPDATED,
                    )

                config = dict(organization.firs_configuration or {})
                config["compliance_sla_hours"] = payload.sla_hours
                config["sla_updated_at"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
                if getattr(context, "user_id", None) is not None:
                    config["sla_updated_by"] = str(context.user_id)

                organization.firs_configuration = config
                session.add(organization)
                await session.commit()
                await session.refresh(organization)

                response_payload = {
                    "slaHours": payload.sla_hours,
                    "updatedAt": config["sla_updated_at"],
                    "updatedBy": config.get("sla_updated_by"),
                }

                return self._create_v1_response(response_payload, self.ACTION_SLA_UPDATED)

            raise RuntimeError("Database session unavailable")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error updating compliance SLA configuration: %s", exc, exc_info=True)
            return v1_error_response(exc, action=self.ACTION_SLA_UPDATED)

    @staticmethod
    def _resolve_sensitive_update(
        incoming: Optional[str], existing: Optional[str]
    ) -> Optional[str]:
        if incoming is None:
            return existing

        incoming_str = str(incoming).strip()
        if not incoming_str:
            return None

        if existing:
            # Treat masked payloads (containing asterisks) as "no change".
            if "*" in incoming_str:
                return existing
            masked_existing = FIRSIntegrationEndpointsV1._mask_secret(existing)
            if incoming_str == masked_existing:
                return existing

        return incoming_str

    @staticmethod
    def _build_safe_configuration_snapshot(config: Dict[str, Any]) -> Dict[str, Any]:
        snapshot = dict(config)
        snapshot["api_key"] = FIRSIntegrationEndpointsV1._mask_secret(config.get("api_key"))
        snapshot["api_secret"] = FIRSIntegrationEndpointsV1._mask_secret(config.get("api_secret"))
        return snapshot

    def _create_v1_response(self, data: Dict[str, Any], action: str) -> V1ResponseModel:
        safe_data = self._make_json_safe(data)
        return build_v1_response(safe_data, action)

    def _make_json_safe(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, (list, tuple, set)):
            return [self._make_json_safe(item) for item in value]
        if isinstance(value, dict):
            return {str(key): self._make_json_safe(val) for key, val in value.items()}
        return value


def create_app_setup_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
) -> APIRouter:
    """Factory for APP setup endpoints."""

    endpoints = APPSetupEndpointsV1(role_detector, permission_guard)
    return endpoints.router
