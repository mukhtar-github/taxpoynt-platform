"""
Unified Error Handler - Hybrid Services
=======================================

Unified error handling across all services (SI, APP, Hybrid).
Integrates with existing error_coordinator, escalation_manager, and incident_tracker.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .error_coordinator import ErrorCoordinator
from .escalation_manager import EscalationManager  
from .incident_tracker import IncidentTracker

logger = logging.getLogger(__name__)


class UnifiedErrorHandler:
    """
    Unified error handling that coordinates existing error management components.
    Provides a single interface for handling errors across all platform services.
    """
    
    def __init__(self):
        self.error_coordinator = ErrorCoordinator()
        self.escalation_manager = EscalationManager()
        self.incident_tracker = IncidentTracker()
        self.error_stats: Dict[str, int] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize unified error handling components"""
        if self.is_initialized:
            return
            
        logger.info("Initializing Unified Error Handler")
        
        # Initialize components
        await self.error_coordinator.initialize()
        await self.escalation_manager.initialize()
        await self.incident_tracker.initialize()
        
        self.is_initialized = True
        logger.info("Unified Error Handler initialized successfully")
    
    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle an error using unified processing across all components"""
        if not self.is_initialized:
            await self.initialize()
            
        error_type = type(error).__name__
        self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
        
        # Use existing error coordinator for initial processing
        coordinator_result = await self.error_coordinator.handle_platform_error(
            error, context or {}
        )
        
        # Create incident using incident tracker
        incident = await self.incident_tracker.create_incident(
            error_type=error_type,
            error_message=str(error),
            context_data=context or {},
            affected_services=[context.get('service', 'unknown')] if context else ['unknown']
        )
        
        # Check if escalation is needed using escalation manager
        escalation_needed = await self.escalation_manager.should_escalate_error(
            error_type, str(error), context or {}
        )
        
        result = {
            'error_id': f"err_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(error))}",
            'error_type': error_type,
            'message': str(error),
            'coordinator_result': coordinator_result,
            'incident_id': incident.incident_id if incident else None,
            'escalation_needed': escalation_needed,
            'timestamp': datetime.now().isoformat(),
            'service': context.get('service', 'unknown') if context else 'unknown'
        }
        
        # Escalate if needed
        if escalation_needed:
            escalation = await self.escalation_manager.create_escalation(
                incident_id=incident.incident_id if incident else result['error_id'],
                escalation_reason=f"Error type: {error_type}",
                context_data=context or {}
            )
            result['escalation_id'] = escalation.escalation_id if escalation else None
        
        return result
    
    async def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error handling summary"""
        if not self.is_initialized:
            await self.initialize()
            
        return {
            'error_coordinator_status': await self.error_coordinator.get_status(),
            'escalation_manager_status': await self.escalation_manager.get_status(), 
            'incident_tracker_status': await self.incident_tracker.get_status(),
            'error_stats': self.error_stats,
            'timestamp': datetime.now().isoformat()
        }
    
    async def handle_platform_wide_error(self, error: Exception, affected_services: list) -> Dict[str, Any]:
        """Handle platform-wide errors affecting multiple services"""
        context = {
            'platform_wide': True,
            'affected_services': affected_services,
            'severity': 'critical'
        }
        
        return await self.handle_error(error, context)