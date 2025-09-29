"""
FIRS SI IRN Generation Service (Refactored)

Refactored service that uses granular components to eliminate duplication.
Maintains backward compatibility while leveraging the new architecture.
"""

import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List, Union, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Import granular components
from .irn_generator import IRNGenerator
from .qr_code_generator import QRCodeGenerator
from .sequence_manager import SequenceManager
from .duplicate_detector import DuplicateDetector
from .irn_validator import IRNValidator, ValidationLevel

from core_platform.utils.firs_response import (
    extract_firs_identifiers,
    map_firs_status_to_submission,
    merge_identifiers_into_payload,
)
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    SubmissionStatus,
)
from core_platform.data_management.models.si_app_correlation import (
    CorrelationStatus,
    SIAPPCorrelation,
)

# Import authentication services for FIRS integration
from si_services.authentication import (
    FIRSAuthService,
    AuthenticationManager,
    AuthenticationError
)

# Legacy imports for backward compatibility
try:  # pragma: no cover - legacy compatibility
    from app.models.irn import IRNRecord, InvoiceData, IRNValidationRecord, IRNStatus  # type: ignore
    from app.models.user import User  # type: ignore
    from app.models.organization import Organization  # type: ignore
    from app.schemas.irn import IRNCreate, IRNBatchGenerateRequest  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - provide lightweight fallbacks for tests
    class _LegacyPlaceholder:  # type: ignore
        def __init__(self, *args, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def __repr__(self) -> str:  # pragma: no cover - debugging aid
            return f"{self.__class__.__name__}({self.__dict__!r})"

    IRNRecord = InvoiceData = IRNValidationRecord = IRNStatus = _LegacyPlaceholder  # type: ignore
    User = Organization = _LegacyPlaceholder  # type: ignore
    IRNCreate = IRNBatchGenerateRequest = _LegacyPlaceholder  # type: ignore

try:
    from app.cache.irn_cache import IRNCache  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - legacy dependency absent in tests
    class IRNCache:  # type: ignore
        def get(self, *_args, **_kwargs):
            return None

        def set(self, *_args, **_kwargs):
            return None

logger = logging.getLogger(__name__)


class IRNGenerationService:
    """
    Refactored IRN Generation Service using granular components.
    
    This service maintains the same interface as the original monolithic service
    but delegates all functionality to the appropriate granular components.
    """
    
    def __init__(self, auth_manager: Optional[AuthenticationManager] = None):
        # Initialize granular components
        self.irn_generator = IRNGenerator()
        self.qr_generator = QRCodeGenerator()
        self.sequence_manager = SequenceManager()
        self.duplicate_detector = DuplicateDetector()
        self.irn_validator = IRNValidator()
        
        # Initialize authentication services for FIRS integration
        self.auth_manager = auth_manager or AuthenticationManager()
        self.firs_auth_service = FIRSAuthService()
        
        # Cache for performance
        self.irn_cache = IRNCache()
    
    def generate_irn(self, invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Generate IRN using granular components (eliminates duplication)
        
        Args:
            invoice_data: Dictionary containing invoice details
            
        Returns:
            Tuple containing (irn_value, verification_code, hash_value)
        """
        try:
            # Check for duplicates first
            existing_irn = self.duplicate_detector.check_duplicate_invoice(invoice_data)
            if existing_irn:
                logger.warning(f"Duplicate invoice detected. Existing IRN: {existing_irn}")
                raise ValueError(f"Invoice already has IRN: {existing_irn}")
            
            # Generate IRN using granular component
            irn_value, verification_code, hash_value = self.irn_generator.generate_irn(invoice_data)
            
            # Validate generated IRN
            validation_result = self.irn_validator.validate_irn(
                irn_value=irn_value,
                verification_code=verification_code,
                validation_level=ValidationLevel.STANDARD
            )
            
            if not validation_result.is_valid:
                error_msg = f"Generated IRN failed validation: {', '.join(validation_result.errors)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Log warnings if any
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"IRN validation warning: {warning}")
            
            # Register IRN to prevent future duplicates
            organization_id = invoice_data.get('organization_id', 'unknown')
            registration_success = self.duplicate_detector.register_irn(
                irn_value=irn_value,
                invoice_data=invoice_data,
                organization_id=organization_id
            )
            
            if not registration_success:
                logger.error("Failed to register IRN for duplicate detection")
                raise ValueError("IRN registration failed")
            
            # Cache the result
            if hasattr(self.irn_cache, 'set'):
                cache_key = f"irn_{irn_value}"
                cache_data = {
                    'irn_value': irn_value,
                    'verification_code': verification_code,
                    'hash_value': hash_value,
                    'generated_at': datetime.now().isoformat()
                }
                self.irn_cache.set(cache_key, cache_data, ttl=3600)  # 1 hour TTL
            
            logger.info(f"Successfully generated IRN: {irn_value} for invoice: {invoice_data.get('invoice_number', '')}")
            
            return irn_value, verification_code, hash_value
            
        except Exception as e:
            logger.error(f"Error generating IRN: {str(e)}")
            raise
    
    async def generate_irn_async(self, invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Async version of IRN generation"""
        return self.generate_irn(invoice_data)
    
    def generate_qr_code(
        self,
        irn_value: str,
        verification_code: str,
        invoice_data: Dict[str, Any],
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate QR code using granular component
        
        Args:
            irn_value: Generated IRN
            verification_code: IRN verification code
            invoice_data: Invoice data
            format_type: QR code format (json, compact, url)
            
        Returns:
            QR code data and image information
        """
        try:
            # Generate QR data
            qr_data = self.qr_generator.generate_qr_data(
                irn_value=irn_value,
                verification_code=verification_code,
                invoice_data=invoice_data
            )
            
            # Generate QR string
            qr_string = self.qr_generator.generate_qr_string(
                irn_value=irn_value,
                verification_code=verification_code,
                invoice_data=invoice_data,
                format_type=format_type
            )
            
            # Generate QR code image
            qr_image_info = self.qr_generator.generate_qr_code_image(qr_string)
            
            result = {
                'qr_data': qr_data,
                'qr_string': qr_string,
                'qr_image': qr_image_info,
                'format_type': format_type,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Generated QR code for IRN: {irn_value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating QR code for IRN {irn_value}: {str(e)}")
            raise
    
    def validate_irn(
        self,
        irn_value: str,
        verification_code: Optional[str] = None,
        validation_level: ValidationLevel = ValidationLevel.STANDARD
    ) -> Dict[str, Any]:
        """
        Validate IRN using granular component
        
        Args:
            irn_value: IRN to validate
            verification_code: Optional verification code
            validation_level: Level of validation
            
        Returns:
            Validation result dictionary
        """
        try:
            validation_result = self.irn_validator.validate_irn(
                irn_value=irn_value,
                verification_code=verification_code,
                validation_level=validation_level
            )
            
            result = {
                'is_valid': validation_result.is_valid,
                'validation_level': validation_result.validation_level.value,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
                'irn_info': validation_result.irn_info,
                'validated_at': datetime.now().isoformat()
            }
            
            if validation_result.errors:
                logger.warning(f"IRN validation failed for {irn_value}: {validation_result.errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error validating IRN {irn_value}: {str(e)}")
            raise
    
    async def get_next_sequence(self, organization_id: str) -> int:
        """Get next sequence number for organization"""
        return await self.sequence_manager.get_next_sequence(organization_id)
    
    def get_irn_info(self, irn_value: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an IRN
        
        Args:
            irn_value: IRN to analyze
            
        Returns:
            IRN information dictionary or None if invalid
        """
        try:
            # Check cache first
            if hasattr(self.irn_cache, 'get'):
                cache_key = f"irn_{irn_value}"
                cached_data = self.irn_cache.get(cache_key)
                if cached_data:
                    return cached_data
            
            # Check in duplicate detector registry
            irn_record = self.duplicate_detector.check_duplicate_irn(irn_value)
            if irn_record:
                return {
                    'irn_value': irn_record.irn_value,
                    'organization_id': irn_record.organization_id,
                    'created_at': irn_record.created_at.isoformat(),
                    'invoice_hash': irn_record.invoice_hash,
                    'invoice_summary': irn_record.invoice_data_summary
                }
            
            # Extract basic info from IRN structure
            validation_result = self.irn_validator.validate_irn(irn_value, validation_level=ValidationLevel.BASIC)
            return validation_result.irn_info
            
        except Exception as e:
            logger.error(f"Error getting IRN info for {irn_value}: {str(e)}")
            return None
    
    async def authenticate_with_firs(
        self,
        environment: str = "sandbox",
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Authenticate with FIRS for IRN submission
        
        Args:
            environment: FIRS environment (sandbox/production)
            credentials: FIRS credentials (optional, can use stored)
            
        Returns:
            Authentication result with session details
        """
        try:
            # Use FIRS authentication service
            auth_result = await self.firs_auth_service.authenticate(
                environment=environment,
                credentials=credentials,
                context={"service": "irn_generation", "purpose": "irn_submission"}
            )
            
            if auth_result.success:
                logger.info(f"Successfully authenticated with FIRS {environment}")
                return {
                    'success': True,
                    'environment': environment,
                    'auth_data': auth_result.auth_data,
                    'session_id': auth_result.session_id,
                    'expires_at': auth_result.expires_at,
                    'authenticated_at': datetime.now().isoformat()
                }
            else:
                logger.error(f"FIRS authentication failed: {auth_result.error_message}")
                return {
                    'success': False,
                    'environment': environment,
                    'error': auth_result.error_message,
                    'attempted_at': datetime.now().isoformat()
                }
                
        except AuthenticationError as e:
            logger.error(f"FIRS authentication error: {e}")
            return {
                'success': False,
                'environment': environment,
                'error': str(e),
                'attempted_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error during FIRS authentication: {e}")
            return {
                'success': False,
                'environment': environment,
                'error': f"Authentication failed: {str(e)}",
                'attempted_at': datetime.now().isoformat()
            }
    
    async def request_irn_from_firs(
        self,
        irn_value: Optional[str],
        invoice_data: Dict[str, Any],
        environment: str = "sandbox",
        *,
        organization_id: Optional[Union[str, uuid.UUID]] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Submit an invoice payload to FIRS and persist returned identifiers."""

        managed_session = False
        session: Optional[AsyncSession] = db_session

        try:
            if session is None:
                async for candidate in get_async_session():
                    session = candidate
                    managed_session = True
                    break

            # Authenticate with FIRS before transmission
            auth_result = await self.authenticate_with_firs(environment)
            if not auth_result["success"]:
                return {
                    "success": False,
                    "error": f"Authentication failed: {auth_result.get('error')}",
                    "irn": irn_value,
                }

            submission_result = await self.firs_auth_service.submit_irn(
                irn_value=irn_value,
                invoice_data=invoice_data,
                auth_data=auth_result["auth_data"],
                environment=environment,
            )

            if not submission_result.success:
                logger.error("FIRS IRN submission failed: %s", submission_result.error_message)
                return {
                    "success": False,
                    "irn": irn_value,
                    "error": submission_result.error_message,
                    "firs_error_code": submission_result.error_code,
                    "submitted_at": datetime.now().isoformat(),
                    "environment": environment,
                }

            logger.info("Successfully submitted invoice to FIRS %s", environment)

            identifiers = extract_firs_identifiers(submission_result.response_data)
            normalized_response = merge_identifiers_into_payload(
                submission_result.response_data or {}, identifiers
            )

            persisted_irn = identifiers.get("irn") or irn_value

            if session:
                try:
                    await self._persist_firs_submission(
                        session,
                        original_irn=irn_value,
                        resolved_irn=persisted_irn,
                        organization_id=organization_id,
                        invoice_data=invoice_data,
                        identifiers=identifiers,
                        response_payload=normalized_response,
                    )
                    if managed_session:
                        await session.commit()
                    else:
                        await session.flush()
                except Exception as persistence_error:
                    if managed_session and session:
                        await session.rollback()
                    logger.error(
                        "Failed to persist FIRS identifiers for invoice %s: %s",
                        persisted_irn,
                        persistence_error,
                        exc_info=True,
                    )

            return {
                "success": True,
                "irn": persisted_irn,
                "firs_response": normalized_response,
                "identifiers": identifiers,
                "submitted_at": datetime.now().isoformat(),
                "environment": environment,
            }

        except Exception as exc:
            if managed_session and session:
                await session.rollback()
            logger.error("Error submitting invoice to FIRS: %s", exc, exc_info=True)
            return {
                "success": False,
                "irn": irn_value,
                "error": str(exc),
                "submitted_at": datetime.now().isoformat(),
                "environment": environment,
            }

    async def submit_irn_to_firs(
        self,
        irn_value: Optional[str],
        invoice_data: Dict[str, Any],
        environment: str = "sandbox",
        *,
        organization_id: Optional[Union[str, uuid.UUID]] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """Backward-compatible wrapper for legacy call sites."""

        logger.debug(
            "submit_irn_to_firs is deprecated; use request_irn_from_firs instead."
        )
        return await self.request_irn_from_firs(
            irn_value=irn_value,
            invoice_data=invoice_data,
            environment=environment,
            organization_id=organization_id,
            db_session=db_session,
        )
    
    async def validate_irn_with_firs(
        self,
        irn_value: str,
        environment: str = "sandbox"
    ) -> Dict[str, Any]:
        """
        Validate IRN with FIRS directly
        
        Args:
            irn_value: IRN to validate
            environment: FIRS environment
            
        Returns:
            FIRS validation result
        """
        try:
            # Authenticate with FIRS
            auth_result = await self.authenticate_with_firs(environment)
            if not auth_result['success']:
                return {
                    'success': False,
                    'error': f"Authentication failed: {auth_result.get('error')}",
                    'irn': irn_value
                }
            
            # Validate with FIRS
            validation_result = await self.firs_auth_service.validate_irn(
                irn_value=irn_value,
                auth_data=auth_result['auth_data'],
                environment=environment
            )
            
            if validation_result.success:
                logger.info(f"IRN {irn_value} validated successfully with FIRS {environment}")
                return {
                    'success': True,
                    'irn': irn_value,
                    'is_valid': validation_result.is_valid,
                    'firs_data': validation_result.response_data,
                    'validated_at': datetime.now().isoformat(),
                    'environment': environment
                }
            else:
                logger.warning(f"FIRS IRN validation failed: {validation_result.error_message}")
                return {
                    'success': False,
                    'irn': irn_value,
                    'error': validation_result.error_message,
                    'validated_at': datetime.now().isoformat(),
                    'environment': environment
                }
                
        except Exception as e:
            logger.error(f"Error validating IRN {irn_value} with FIRS: {e}")
            return {
                'success': False,
                'irn': irn_value,
                'error': str(e),
                'validated_at': datetime.now().isoformat(),
                'environment': environment
            }

    async def _persist_firs_submission(
        self,
        session: AsyncSession,
        *,
        original_irn: Optional[str],
        resolved_irn: Optional[str],
        organization_id: Optional[Union[str, uuid.UUID]],
        invoice_data: Dict[str, Any],
        identifiers: Dict[str, Any],
        response_payload: Dict[str, Any],
    ) -> None:
        """Persist FIRS identifiers onto the submission + correlation records."""

        org_uuid = self._resolve_organization_id(organization_id, invoice_data)
        invoice_number = self._resolve_invoice_number(invoice_data)
        submission_id = self._extract_submission_id(invoice_data)

        submission = await self._resolve_submission(
            session,
            submission_id=submission_id,
            organization_id=org_uuid,
            invoice_number=invoice_number,
            irn=original_irn,
        )

        if not submission:
            logger.warning(
                "Unable to locate FIRS submission for invoice_number=%s irn=%s",
                invoice_number,
                original_irn,
            )
            return

        status_text = identifiers.get("status") or response_payload.get("status")
        mapped_status = map_firs_status_to_submission(status_text)

        try:
            status_enum = SubmissionStatus(mapped_status)
        except ValueError:
            status_enum = SubmissionStatus.SUBMITTED

        previous_irn = submission.irn

        submission.update_status(
            status_enum,
            status_text or mapped_status,
            response_payload,
        )

        if resolved_irn:
            submission.irn = resolved_irn

        if invoice_data and isinstance(invoice_data, dict):
            merged_invoice = dict(invoice_data)
            if resolved_irn:
                merged_invoice.setdefault("irn", resolved_irn)
            submission.invoice_data = merged_invoice
        elif resolved_irn:
            submission.invoice_data = {"irn": resolved_irn}

        await session.flush()

        await self._update_correlation(
            session,
            previous_irn=previous_irn or original_irn,
            resolved_irn=resolved_irn,
            organization_id=org_uuid,
            status_label=mapped_status,
            response_payload=response_payload,
            identifiers=identifiers,
            invoice_number=invoice_number,
        )

    async def _resolve_submission(
        self,
        session: AsyncSession,
        *,
        submission_id: Optional[Union[str, uuid.UUID]],
        organization_id: Optional[uuid.UUID],
        invoice_number: Optional[str],
        irn: Optional[str],
    ) -> Optional[FIRSSubmission]:
        if submission_id:
            stmt = select(FIRSSubmission).where(FIRSSubmission.id == submission_id)
            if organization_id:
                stmt = stmt.where(FIRSSubmission.organization_id == organization_id)
            result = await session.execute(stmt)
            submission = result.scalars().first()
            if submission:
                return submission

        if irn:
            stmt = select(FIRSSubmission).where(FIRSSubmission.irn == irn)
            if organization_id:
                stmt = stmt.where(FIRSSubmission.organization_id == organization_id)
            result = await session.execute(stmt)
            submission = result.scalars().first()
            if submission:
                return submission

        if invoice_number:
            stmt = select(FIRSSubmission).where(FIRSSubmission.invoice_number == invoice_number)
            if organization_id:
                stmt = stmt.where(FIRSSubmission.organization_id == organization_id)
            result = await session.execute(stmt)
            submission = result.scalars().first()
            if submission:
                return submission

        return None

    async def _update_correlation(
        self,
        session: AsyncSession,
        *,
        previous_irn: Optional[str],
        resolved_irn: Optional[str],
        organization_id: Optional[uuid.UUID],
        status_label: str,
        response_payload: Dict[str, Any],
        identifiers: Dict[str, Any],
        invoice_number: Optional[str],
    ) -> None:
        candidates: List[str] = []
        if resolved_irn:
            candidates.append(resolved_irn)
        if previous_irn and previous_irn not in candidates:
            candidates.append(previous_irn)

        correlation: Optional[SIAPPCorrelation] = None
        for candidate in candidates:
            stmt = select(SIAPPCorrelation).where(SIAPPCorrelation.irn == candidate)
            if organization_id:
                stmt = stmt.where(SIAPPCorrelation.organization_id == organization_id)
            result = await session.execute(stmt.limit(1))
            correlation = result.scalars().first()
            if correlation:
                break

        if not correlation:
            return

        if resolved_irn and correlation.irn != resolved_irn:
            correlation.irn = resolved_irn

        if invoice_number and correlation.invoice_number != invoice_number:
            correlation.invoice_number = invoice_number

        firs_response_id = (
            identifiers.get("response_id")
            or response_payload.get("submissionId")
            or response_payload.get("submission_id")
        )

        status_for_correlation = status_label or CorrelationStatus.APP_SUBMITTED.value
        correlation.set_firs_response(
            firs_response_id or resolved_irn or previous_irn,
            status_for_correlation,
            response_payload,
        )

        if identifiers:
            metadata = correlation.submission_metadata or {}
            metadata["identifiers"] = identifiers
            correlation.submission_metadata = metadata

        await session.flush()

    def _resolve_organization_id(
        self,
        organization_id: Optional[Union[str, uuid.UUID]],
        invoice_data: Dict[str, Any],
    ) -> Optional[uuid.UUID]:
        candidates: List[Optional[Union[str, uuid.UUID]]] = [organization_id]

        if isinstance(invoice_data, dict):
            candidates.append(invoice_data.get("organization_id"))
            candidates.append(invoice_data.get("organizationId"))
            candidates.append(invoice_data.get("tenant_id"))
            candidates.append(invoice_data.get("tenantId"))
            metadata = invoice_data.get("metadata")
            if isinstance(metadata, dict):
                candidates.append(metadata.get("organization_id"))
                candidates.append(metadata.get("organizationId"))

        for candidate in candidates:
            parsed = self._try_parse_uuid(candidate)
            if parsed:
                return parsed

        return None

    def _resolve_invoice_number(self, invoice_data: Dict[str, Any]) -> Optional[str]:
        if not isinstance(invoice_data, dict):
            return None

        keys = [
            "invoice_number",
            "invoiceNumber",
            "invoice_id",
            "invoiceId",
            "irn",
        ]

        for key in keys:
            value = invoice_data.get(key)
            if value:
                return str(value)

        metadata = invoice_data.get("metadata")
        if isinstance(metadata, dict):
            for key in keys:
                value = metadata.get(key)
                if value:
                    return str(value)

        return None

    def _extract_submission_id(self, invoice_data: Dict[str, Any]) -> Optional[uuid.UUID]:
        if not isinstance(invoice_data, dict):
            return None

        candidates = [
            invoice_data.get("submission_id"),
            invoice_data.get("submissionId"),
            invoice_data.get("firs_submission_id"),
            invoice_data.get("firsSubmissionId"),
        ]

        metadata = invoice_data.get("metadata")
        if isinstance(metadata, dict):
            candidates.extend(
                [
                    metadata.get("submission_id"),
                    metadata.get("submissionId"),
                    metadata.get("firs_submission_id"),
                ]
            )

        for candidate in candidates:
            parsed = self._try_parse_uuid(candidate)
            if parsed:
                return parsed

        return None

    def _try_parse_uuid(
        self, value: Optional[Union[str, uuid.UUID]]
    ) -> Optional[uuid.UUID]:
        if not value:
            return None
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(str(value))
        except Exception:
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'duplicate_detection': self.duplicate_detector.get_statistics(),
            'sequence_manager': self.sequence_manager.export_sequence_state(),
            'service_info': {
                'components_loaded': True,
                'cache_enabled': hasattr(self.irn_cache, 'get'),
                'timestamp': datetime.now().isoformat()
            }
        }


# Backward compatibility functions (delegate to service instance)
_service_instance = None

def get_service_instance() -> IRNGenerationService:
    """Get singleton service instance"""
    global _service_instance
    if _service_instance is None:
        _service_instance = IRNGenerationService()
    return _service_instance

def generate_irn(invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Backward compatibility function for generate_irn
    
    This maintains the original function signature while using the new architecture.
    """
    service = get_service_instance()
    return service.generate_irn(invoice_data)

def validate_irn_format(irn_value: str) -> bool:
    """Backward compatibility function for IRN format validation"""
    service = get_service_instance()
    validation_result = service.validate_irn(irn_value, validation_level=ValidationLevel.BASIC)
    return validation_result['is_valid']

def get_irn_expiration_date(irn_value: str) -> Optional[datetime]:
    """Backward compatibility function for IRN expiration"""
    service = get_service_instance()
    irn_info = service.get_irn_info(irn_value)
    
    if irn_info and 'timestamp' in irn_info:
        # Assume 1 year expiration from generation
        try:
            generation_time = datetime.fromisoformat(irn_info['timestamp'])
            return generation_time + timedelta(days=365)
        except (ValueError, TypeError):
            pass
    
    return None

def create_validation_record(irn_value: str, validation_result: Dict[str, Any]) -> IRNValidationRecord:
    """Backward compatibility function for creating validation records"""
    # This would need to be adapted based on your actual model structure
    return IRNValidationRecord(
        irn_value=irn_value,
        is_valid=validation_result.get('is_valid', False),
        validation_errors=validation_result.get('errors', []),
        validated_at=datetime.now()
    )
