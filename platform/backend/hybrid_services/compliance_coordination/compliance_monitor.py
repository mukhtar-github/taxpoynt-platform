"""
Cross-Role Compliance Monitor - Hybrid Services
===============================================

Monitors compliance across SI and APP services.
Integrates with existing compliance_orchestrator and cross_role_validator.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, field

from .compliance_orchestrator import ComplianceOrchestrator
from .cross_role_validator import CrossRoleValidator

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """Compliance check result"""
    rule_id: str
    passed: bool
    score: float
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class CrossRoleComplianceMonitor:
    """
    Monitors compliance across SI and APP services.
    Coordinates with existing compliance orchestrator and validator.
    """
    
    def __init__(self):
        self.compliance_orchestrator = ComplianceOrchestrator()
        self.cross_role_validator = CrossRoleValidator()
        self.compliance_cache: Dict[str, ComplianceResult] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize compliance monitoring components"""
        if self.is_initialized:
            return
            
        logger.info("Initializing Cross-Role Compliance Monitor")
        
        # Initialize components
        await self.compliance_orchestrator.initialize()
        await self.cross_role_validator.initialize()
        
        self.is_initialized = True
        logger.info("Cross-Role Compliance Monitor initialized successfully")
    
    async def monitor_compliance(self, service: str, data: Dict[str, Any]) -> ComplianceResult:
        """Monitor compliance for a service"""
        if not self.is_initialized:
            await self.initialize()
            
        # Use existing orchestrator for comprehensive compliance check
        orchestrator_result = await self.compliance_orchestrator.execute_compliance_check(
            service, data
        )
        
        # Use existing validator for cross-role validation
        validation_result = await self.cross_role_validator.validate_cross_role_operation(
            service, data
        )
        
        # Combine results
        combined_score = (
            orchestrator_result.get('compliance_score', 0.0) + 
            validation_result.get('validation_score', 0.0)
        ) / 2
        
        result = ComplianceResult(
            rule_id=f"{service}_combined_compliance",
            passed=combined_score >= 0.7,
            score=combined_score,
            details={
                'orchestrator_result': orchestrator_result,
                'validation_result': validation_result,
                'service': service
            }
        )
        
        # Cache result
        cache_key = f"{service}_{hash(str(data))}"
        self.compliance_cache[cache_key] = result
        
        return result
    
    async def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance monitoring summary"""
        if not self.is_initialized:
            await self.initialize()
            
        return {
            'orchestrator_status': await self.compliance_orchestrator.get_status(),
            'validator_status': await self.cross_role_validator.get_status(),
            'cached_results': len(self.compliance_cache),
            'timestamp': datetime.now().isoformat()
        }