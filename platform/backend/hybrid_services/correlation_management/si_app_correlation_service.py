"""
SI-APP Correlation Management Service
====================================
Service for managing correlations between SI invoice generation and APP FIRS submissions.
This enables status synchronization and tracking across role boundaries.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload

from core_platform.data_management.models.si_app_correlation import SIAPPCorrelation, CorrelationStatus
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.models.firs_submission import FIRSSubmission, SubmissionStatus
from core_platform.utils.firs_response import (
    extract_firs_identifiers,
    merge_identifiers_into_payload,
    map_firs_status_to_submission,
)

logger = logging.getLogger(__name__)


class SIAPPCorrelationService:
    """
    Service for managing SI-APP correlations and status synchronization.
    
    Key Features:
    - Create correlations when SI generates invoices
    - Update status when APP receives/submits invoices
    - Sync status back to SI when FIRS responds
    - Provide correlation tracking and analytics
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        
    async def create_correlation(
        self,
        organization_id: UUID,
        si_invoice_id: str,
        si_transaction_ids: List[str],
        irn: str,
        invoice_number: str,
        total_amount: float,
        currency: str,
        customer_name: str,
        customer_email: Optional[str] = None,
        customer_tin: Optional[str] = None,
        invoice_data: Optional[Dict] = None
    ) -> SIAPPCorrelation:
        """
        Create a new SI-APP correlation when SI generates an invoice.
        
        Args:
            organization_id: Organization UUID
            si_invoice_id: SI-generated invoice identifier
            si_transaction_ids: List of transaction IDs from SI
            irn: Generated IRN
            invoice_number: Invoice number
            total_amount: Invoice total amount
            currency: Invoice currency
            customer_name: Customer name
            customer_email: Customer email (optional)
            customer_tin: Customer TIN (optional)
            invoice_data: Full invoice data (optional)
            
        Returns:
            Created SIAPPCorrelation instance
        """
        try:
            correlation = SIAPPCorrelation(
                organization_id=organization_id,
                si_invoice_id=si_invoice_id,
                si_transaction_ids=si_transaction_ids,
                irn=irn,
                si_generated_at=datetime.utcnow(),
                invoice_number=invoice_number,
                total_amount=total_amount,
                currency=currency,
                customer_name=customer_name,
                customer_email=customer_email,
                customer_tin=customer_tin,
                invoice_data=invoice_data,
                current_status=CorrelationStatus.SI_GENERATED,
                last_status_update=datetime.utcnow()
            )
            
            self.db.add(correlation)
            await self.db.commit()
            await self.db.refresh(correlation)
            
            logger.info(f"Created SI-APP correlation {correlation.correlation_id} for IRN {irn}")
            return correlation
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create SI-APP correlation: {e}")
            raise
    
    async def get_correlation_by_irn(self, irn: str) -> Optional[SIAPPCorrelation]:
        """Get correlation by IRN."""
        result = await self.db.execute(
            select(SIAPPCorrelation)
            .where(SIAPPCorrelation.irn == irn)
            .options(selectinload(SIAPPCorrelation.organization))
        )
        return result.scalar_one_or_none()
    
    async def get_correlation_by_id(self, correlation_id: str) -> Optional[SIAPPCorrelation]:
        """Get correlation by correlation ID."""
        result = await self.db.execute(
            select(SIAPPCorrelation)
            .where(SIAPPCorrelation.correlation_id == correlation_id)
            .options(selectinload(SIAPPCorrelation.organization))
        )
        return result.scalar_one_or_none()
    
    async def update_app_received(
        self,
        irn: str,
        app_submission_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update correlation when APP receives the invoice for submission.
        
        Args:
            irn: Invoice Reference Number
            app_submission_id: APP submission identifier
            metadata: Additional metadata
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            correlation = await self.get_correlation_by_irn(irn)
            if not correlation:
                logger.warning(f"Correlation not found for IRN {irn}")
                return False
            
            correlation.set_app_received(app_submission_id, metadata)
            await self.db.commit()
            
            logger.info(f"Updated correlation {correlation.correlation_id} - APP received")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update APP received status for IRN {irn}: {e}")
            return False
    
    async def update_app_submitting(self, irn: str, metadata: Optional[Dict] = None) -> bool:
        """Update correlation when APP starts submitting to FIRS."""
        try:
            correlation = await self.get_correlation_by_irn(irn)
            if not correlation:
                logger.warning(f"Correlation not found for IRN {irn}")
                return False
            
            correlation.set_app_submitting(metadata)
            await self.db.commit()
            
            logger.info(f"Updated correlation {correlation.correlation_id} - APP submitting")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update APP submitting status for IRN {irn}: {e}")
            return False
    
    async def update_app_submitted(self, irn: str, metadata: Optional[Dict] = None) -> bool:
        """Update correlation when APP completes submission to FIRS."""
        try:
            correlation = await self.get_correlation_by_irn(irn)
            if not correlation:
                logger.warning(f"Correlation not found for IRN {irn}")
                return False
            
            correlation.set_app_submitted(metadata)
            await self.db.commit()
            
            logger.info(f"Updated correlation {correlation.correlation_id} - APP submitted")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update APP submitted status for IRN {irn}: {e}")
            return False
    
    async def update_firs_response(
        self,
        irn: str,
        firs_response_id: Optional[str],
        firs_status: str,
        response_data: Optional[Dict] = None,
        identifiers: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update correlation with FIRS response.
        
        Args:
            irn: Invoice Reference Number
            firs_response_id: FIRS response identifier
            firs_status: FIRS status (accepted/rejected/etc.)
            response_data: Full FIRS response data
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            correlation = await self.get_correlation_by_irn(irn)
            if not correlation:
                logger.warning(f"Correlation not found for IRN {irn}")
                return False
            
            correlation.set_firs_response(firs_response_id, firs_status, response_data, metadata)

            if metadata:
                submission_meta = correlation.submission_metadata or {}
                timeline = submission_meta.get("timeline")
                if isinstance(timeline, list):
                    timeline = timeline + [metadata]
                else:
                    timeline = [metadata]
                submission_meta["timeline"] = timeline
                correlation.submission_metadata = submission_meta

            submission = await self._get_firs_submission(irn, correlation)
            if submission:
                merged_payload = response_data or {}
                if identifiers:
                    merged_payload = merge_identifiers_into_payload(merged_payload, identifiers)
                else:
                    normalized = extract_firs_identifiers(merged_payload)
                    if normalized:
                        merged_payload = merge_identifiers_into_payload(merged_payload, normalized)
                        identifiers = normalized

                status_label = map_firs_status_to_submission(firs_status)
                submission_status = self._map_submission_status(status_label, submission.status)
                submission.update_status(submission_status, firs_status, merged_payload)

            await self.db.commit()
            
            logger.info(f"Updated correlation {correlation.correlation_id} - FIRS response: {firs_status}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update FIRS response for IRN {irn}: {e}")
            return False

    async def _get_firs_submission(
        self,
        irn: str,
        correlation: Optional[SIAPPCorrelation]
    ) -> Optional[FIRSSubmission]:
        submission = None
        if irn:
            result = await self.db.execute(
                select(FIRSSubmission).where(FIRSSubmission.irn == irn)
            )
            submission = result.scalar_one_or_none()

        if not submission and correlation:
            result = await self.db.execute(
                select(FIRSSubmission).where(
                    and_(
                        FIRSSubmission.organization_id == correlation.organization_id,
                        FIRSSubmission.invoice_number == correlation.invoice_number
                    )
                )
            )
            submission = result.scalar_one_or_none()

        if submission and not submission.irn and irn:
            submission.irn = irn

        return submission

    def _map_submission_status(
        self,
        status_label: str,
        current_status: SubmissionStatus
    ) -> SubmissionStatus:
        normalized = (status_label or "").lower()
        if normalized in {"accepted", "success", "approved"}:
            return SubmissionStatus.ACCEPTED
        if normalized in {"rejected", "failed", "error"}:
            return SubmissionStatus.REJECTED
        if normalized in {"processing", "pending", "queued"}:
            return SubmissionStatus.PROCESSING
        if normalized in {"submitted", "transmitted"}:
            return SubmissionStatus.SUBMITTED
        return current_status
    
    async def get_organization_correlations(
        self,
        organization_id: UUID,
        status: Optional[CorrelationStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SIAPPCorrelation]:
        """Get correlations for an organization."""
        query = select(SIAPPCorrelation).where(
            SIAPPCorrelation.organization_id == organization_id
        ).options(selectinload(SIAPPCorrelation.organization))
        
        if status:
            query = query.where(SIAPPCorrelation.current_status == status)
        
        query = query.order_by(SIAPPCorrelation.si_generated_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_pending_correlations(self, limit: int = 100) -> List[SIAPPCorrelation]:
        """Get correlations that are pending APP processing."""
        result = await self.db.execute(
            select(SIAPPCorrelation)
            .where(SIAPPCorrelation.current_status.in_([
                CorrelationStatus.SI_GENERATED,
                CorrelationStatus.APP_RECEIVED,
                CorrelationStatus.APP_SUBMITTING
            ]))
            .order_by(SIAPPCorrelation.si_generated_at.asc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_stale_correlations(self, hours: int = 24) -> List[SIAPPCorrelation]:
        """Get correlations that haven't been updated in specified hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(SIAPPCorrelation)
            .where(
                and_(
                    SIAPPCorrelation.last_status_update < cutoff_time,
                    SIAPPCorrelation.current_status.not_in([
                        CorrelationStatus.FIRS_ACCEPTED,
                        CorrelationStatus.FIRS_REJECTED,
                        CorrelationStatus.FAILED,
                        CorrelationStatus.CANCELLED
                    ])
                )
            )
        )
        return result.scalars().all()
    
    async def get_correlation_statistics(
        self,
        organization_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get correlation statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        base_query = select(SIAPPCorrelation).where(
            SIAPPCorrelation.si_generated_at >= cutoff_date
        )
        
        if organization_id:
            base_query = base_query.where(SIAPPCorrelation.organization_id == organization_id)
        
        # Get all correlations
        result = await self.db.execute(base_query)
        correlations = result.scalars().all()
        
        if not correlations:
            return {
                'total_correlations': 0,
                'status_breakdown': {},
                'success_rate': 0.0,
                'average_processing_time': 0,
                'period_days': days
            }
        
        # Calculate statistics
        status_counts = {}
        processing_times = []
        
        for correlation in correlations:
            status = correlation.current_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if correlation.processing_duration > 0:
                processing_times.append(correlation.processing_duration)
        
        success_count = status_counts.get(CorrelationStatus.FIRS_ACCEPTED.value, 0)
        success_rate = (success_count / len(correlations)) * 100 if correlations else 0
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'total_correlations': len(correlations),
            'status_breakdown': status_counts,
            'success_rate': round(success_rate, 2),
            'average_processing_time': round(avg_processing_time, 2),
            'period_days': days
        }
    
    async def cleanup_old_correlations(self, days: int = 90) -> int:
        """Clean up old completed correlations."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        result = await self.db.execute(
            update(SIAPPCorrelation)
            .where(
                and_(
                    SIAPPCorrelation.last_status_update < cutoff_date,
                    SIAPPCorrelation.current_status.in_([
                        CorrelationStatus.FIRS_ACCEPTED,
                        CorrelationStatus.FIRS_REJECTED,
                        CorrelationStatus.FAILED,
                        CorrelationStatus.CANCELLED
                    ])
                )
            )
            .values(
                invoice_data=None,  # Clear large JSON data
                submission_metadata=None,
                firs_response_data=None
            )
        )
        
        await self.db.commit()
        cleaned_count = result.rowcount
        
        logger.info(f"Cleaned up {cleaned_count} old correlations")
        return cleaned_count
    
    async def retry_failed_correlation(self, correlation_id: str) -> bool:
        """Retry a failed correlation."""
        try:
            correlation = await self.get_correlation_by_id(correlation_id)
            if not correlation:
                logger.warning(f"Correlation {correlation_id} not found for retry")
                return False
            
            if not correlation.can_retry():
                logger.warning(f"Correlation {correlation_id} has exceeded max retries")
                return False
            
            correlation.increment_retry()
            correlation.update_status(
                CorrelationStatus.SI_GENERATED,
                {'retry': True, 'retry_count': correlation.retry_count}
            )
            
            await self.db.commit()
            logger.info(f"Queued correlation {correlation_id} for retry")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to retry correlation {correlation_id}: {e}")
            return False
