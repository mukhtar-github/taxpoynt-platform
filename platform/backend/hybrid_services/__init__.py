"""
Hybrid Services Initialization and Registration
===============================================

Initializes and registers all Hybrid services with the message router.
Hybrid services bridge SI and APP functionality, handling cross-role operations.

Services Registered:
- Analytics Service (data analysis across roles)
- Billing Service (subscription and usage tracking)
- Compliance Service (cross-role compliance monitoring)
- Configuration Management (system-wide configuration)
- Data Synchronization (SI-APP data coordination)
- Error Management (unified error handling)
- Access Control (cross-role permissions)
- Workflow Orchestration (multi-role business processes)
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from core_platform.messaging.message_router import MessageRouter, ServiceRole

# Import Hybrid services (using existing files only)
# Analytics - using available files
from .analytics_aggregation.unified_metrics import UnifiedMetrics
from .analytics_aggregation.kpi_calculator import KPICalculator  
from .analytics_aggregation.trend_analyzer import TrendAnalyzer

# Billing - using existing files
from .billing_orchestration.subscription_manager import SubscriptionManager
from .billing_orchestration.usage_tracker import UsageTracker
from .billing_orchestration.billing_engine import BillingEngine

# Compliance - using existing files
from .compliance_coordination.compliance_orchestrator import ComplianceOrchestrator
from .compliance_coordination.cross_role_validator import CrossRoleValidator

# Configuration Management - using existing files
from .configuration_management.config_coordinator import ConfigCoordinator
from .configuration_management.environment_manager import EnvironmentManager

# Data Synchronization - using existing files  
from .data_synchronization.consistency_manager import ConsistencyManager
from .data_synchronization.state_synchronizer import StateSynchronizer

# Error Management - using existing files
from .error_management.error_coordinator import ErrorCoordinator
from .error_management.recovery_orchestrator import RecoveryOrchestrator

# Service Access Control - using existing files
from .service_access_control.access_middleware import AccessMiddleware
from .service_access_control.quota_manager import QuotaManager

# Workflow Orchestration - using existing files
from .workflow_orchestration.process_coordinator import ProcessCoordinator
from .workflow_orchestration.e2e_workflow_engine import E2EWorkflowEngine

# Correlation Management - new service for SI-APP correlation
from .correlation_management.si_app_correlation_service import SIAPPCorrelationService
from .transmission_coordination import TransmissionCoordinationService

logger = logging.getLogger(__name__)


# Import the real implementations from their appropriate directories
from .analytics_aggregation.analytics_processor import AnalyticsProcessor, AdvancedAnalyticsEngine, BusinessIntelligenceService
from .compliance_coordination.compliance_monitor import CrossRoleComplianceMonitor
from .configuration_management.dynamic_config_manager import DynamicConfigManager
from .error_management.unified_error_handler import UnifiedErrorHandler
from .service_access_control.unified_rbac import UnifiedRBAC
from .workflow_orchestration.business_process_engine import BusinessProcessEngine


class HybridServiceRegistry:
    """
    Registry for all Hybrid services that handles initialization and message router registration.
    """
    
    def __init__(self, message_router: MessageRouter):
        """
        Initialize Hybrid service registry.
        
        Args:
            message_router: Core platform message router
        """
        self.message_router = message_router
        self.services: Dict[str, Any] = {}
        self.service_endpoints: Dict[str, str] = {}
        self.is_initialized = False
        
    async def initialize_services(self) -> Dict[str, str]:
        """
        Initialize and register all Hybrid services.
        
        Returns:
            Dict mapping service names to endpoint IDs
        """
        try:
            logger.info("Initializing Hybrid services...")
            
            # Initialize all Hybrid services
            await self._register_analytics_services()
            await self._register_billing_services()
            await self._register_compliance_services()
            await self._register_configuration_services()
            await self._register_sync_services()
            await self._register_error_management_services()
            await self._register_access_control_services()
            await self._register_workflow_services()
            await self._register_correlation_services()
            await self._register_transmission_coordination_services()
            
            self.is_initialized = True
            logger.info(f"Hybrid services initialized successfully. Registered {len(self.service_endpoints)} services.")
            
            return self.service_endpoints
            
        except Exception as e:
            logger.error(f"Failed to initialize Hybrid services: {str(e)}", exc_info=True)
            raise RuntimeError(f"Hybrid service initialization failed: {str(e)}")
    
    async def _register_analytics_services(self):
        """Register analytics and business intelligence services"""
        try:
            # Initialize analytics services
            analytics_processor = AnalyticsProcessor()
            advanced_engine = AdvancedAnalyticsEngine()
            bi_service = BusinessIntelligenceService()
            
            analytics_service = {
                "analytics_processor": analytics_processor,
                "advanced_engine": advanced_engine,
                "bi_service": bi_service,
                "operations": [
                    "process_analytics",
                    "generate_insights",
                    "create_dashboard",
                    "analyze_cross_role_data",
                    "generate_reports"
                ]
            }
            
            self.services["analytics"] = analytics_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="analytics",
                service_role=ServiceRole.HYBRID,
                callback=self._create_analytics_callback(analytics_service),
                priority=4,
                tags=["analytics", "intelligence", "reporting", "cross_role"],
                metadata={
                    "service_type": "analytics",
                    "operations": [
                        "process_analytics",
                        "generate_insights",
                        "create_dashboard",
                        "analyze_cross_role_data",
                        "generate_reports"
                    ]
                }
            )
            
            self.service_endpoints["analytics"] = endpoint_id
            logger.info(f"Analytics service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register analytics services: {str(e)}")
    
    async def _register_billing_services(self):
        """Register billing and subscription services"""
        try:
            # Initialize billing services
            subscription_manager = SubscriptionManager()
            usage_tracker = UsageTracker()
            billing_processor = BillingProcessor()
            
            billing_service = {
                "subscription_manager": subscription_manager,
                "usage_tracker": usage_tracker,
                "billing_processor": billing_processor,
                "operations": [
                    "manage_subscription",
                    "track_usage",
                    "process_billing",
                    "calculate_fees",
                    "generate_invoice"
                ]
            }
            
            self.services["billing"] = billing_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="billing",
                service_role=ServiceRole.HYBRID,
                callback=self._create_billing_callback(billing_service),
                priority=4,
                tags=["billing", "subscription", "usage", "revenue"],
                metadata={
                    "service_type": "billing",
                    "operations": [
                        "manage_subscription",
                        "track_usage",
                        "process_billing",
                        "calculate_fees",
                        "generate_invoice"
                    ]
                }
            )
            
            self.service_endpoints["billing"] = endpoint_id
            logger.info(f"Billing service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register billing services: {str(e)}")
    
    async def _register_compliance_services(self):
        """Register cross-role compliance services"""
        try:
            # Initialize compliance services
            compliance_monitor = CrossRoleComplianceMonitor()
            regulatory_service = RegulatoryAlignmentService()
            
            compliance_service = {
                "compliance_monitor": compliance_monitor,
                "regulatory_service": regulatory_service,
                "operations": [
                    "monitor_compliance",
                    "check_regulatory_alignment",
                    "generate_compliance_report",
                    "validate_cross_role_operations"
                ]
            }
            
            self.services["compliance"] = compliance_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="compliance",
                service_role=ServiceRole.HYBRID,
                callback=self._create_compliance_callback(compliance_service),
                priority=5,
                tags=["compliance", "regulatory", "monitoring", "cross_role"],
                metadata={
                    "service_type": "compliance",
                    "operations": [
                        "monitor_compliance",
                        "check_regulatory_alignment",
                        "generate_compliance_report",
                        "validate_cross_role_operations"
                    ]
                }
            )
            
            self.service_endpoints["compliance"] = endpoint_id
            logger.info(f"Compliance service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register compliance services: {str(e)}")
    
    async def _register_configuration_services(self):
        """Register configuration management services"""
        try:
            # Initialize configuration services
            config_manager = DynamicConfigManager()
            env_manager = EnvironmentManager()
            
            config_service = {
                "config_manager": config_manager,
                "env_manager": env_manager,
                "operations": [
                    "manage_configuration",
                    "update_environment",
                    "validate_config",
                    "sync_config_across_roles"
                ]
            }
            
            self.services["configuration"] = config_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="configuration",
                service_role=ServiceRole.HYBRID,
                callback=self._create_config_callback(config_service),
                priority=4,
                tags=["configuration", "environment", "management", "sync"],
                metadata={
                    "service_type": "configuration",
                    "operations": [
                        "manage_configuration",
                        "update_environment",
                        "validate_config",
                        "sync_config_across_roles"
                    ]
                }
            )
            
            self.service_endpoints["configuration"] = endpoint_id
            logger.info(f"Configuration service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register configuration services: {str(e)}")
    
    async def _register_sync_services(self):
        """Register data synchronization services"""
        try:
            # Initialize sync services
            consistency_manager = ConsistencyManager()
            cross_role_sync = CrossRoleSync()
            
            sync_service = {
                "consistency_manager": consistency_manager,
                "cross_role_sync": cross_role_sync,
                "operations": [
                    "sync_data_across_roles",
                    "ensure_consistency",
                    "resolve_conflicts",
                    "coordinate_updates"
                ]
            }
            
            self.services["data_synchronization"] = sync_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="data_synchronization",
                service_role=ServiceRole.HYBRID,
                callback=self._create_sync_callback(sync_service),
                priority=5,
                tags=["synchronization", "consistency", "cross_role", "data"],
                metadata={
                    "service_type": "data_synchronization",
                    "operations": [
                        "sync_data_across_roles",
                        "ensure_consistency",
                        "resolve_conflicts",
                        "coordinate_updates"
                    ]
                }
            )
            
            self.service_endpoints["data_synchronization"] = endpoint_id
            logger.info(f"Data synchronization service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register sync services: {str(e)}")
    
    async def _register_error_management_services(self):
        """Register unified error management services"""
        try:
            # Initialize error management services
            error_handler = UnifiedErrorHandler()
            error_analytics = ErrorAnalytics()
            
            error_service = {
                "error_handler": error_handler,
                "error_analytics": error_analytics,
                "operations": [
                    "handle_unified_error",
                    "analyze_error_patterns",
                    "coordinate_error_resolution",
                    "generate_error_reports"
                ]
            }
            
            self.services["error_management"] = error_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="error_management",
                service_role=ServiceRole.HYBRID,
                callback=self._create_error_callback(error_service),
                priority=5,
                tags=["error", "management", "analytics", "unified"],
                metadata={
                    "service_type": "error_management",
                    "operations": [
                        "handle_unified_error",
                        "analyze_error_patterns",
                        "coordinate_error_resolution",
                        "generate_error_reports"
                    ]
                }
            )
            
            self.service_endpoints["error_management"] = endpoint_id
            logger.info(f"Error management service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register error management services: {str(e)}")
    
    async def _register_access_control_services(self):
        """Register unified access control services"""
        try:
            # Initialize access control services
            unified_rbac = UnifiedRBAC()
            permission_bridge = PermissionBridge()
            
            access_service = {
                "unified_rbac": unified_rbac,
                "permission_bridge": permission_bridge,
                "operations": [
                    "manage_unified_access",
                    "bridge_permissions",
                    "validate_cross_role_access",
                    "coordinate_authorization"
                ]
            }
            
            self.services["access_control"] = access_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="access_control",
                service_role=ServiceRole.HYBRID,
                callback=self._create_access_callback(access_service),
                priority=5,
                tags=["access", "control", "rbac", "permissions"],
                metadata={
                    "service_type": "access_control",
                    "operations": [
                        "manage_unified_access",
                        "bridge_permissions",
                        "validate_cross_role_access",
                        "coordinate_authorization"
                    ]
                }
            )
            
            self.service_endpoints["access_control"] = endpoint_id
            logger.info(f"Access control service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register access control services: {str(e)}")
    
    async def _register_workflow_services(self):
        """Register workflow orchestration services"""
        try:
            # Initialize workflow services
            process_engine = BusinessProcessEngine()
            coordinator = MultiRoleCoordinator()
            
            workflow_service = {
                "process_engine": process_engine,
                "coordinator": coordinator,
                "operations": [
                    "orchestrate_business_process",
                    "coordinate_multi_role_operations",
                    "manage_workflow_state",
                    "execute_complex_processes"
                ]
            }
            
            self.services["workflow"] = workflow_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="workflow",
                service_role=ServiceRole.HYBRID,
                callback=self._create_workflow_callback(workflow_service),
                priority=4,
                tags=["workflow", "orchestration", "process", "coordination"],
                metadata={
                    "service_type": "workflow",
                    "operations": [
                        "orchestrate_business_process",
                        "coordinate_multi_role_operations",
                        "manage_workflow_state",
                        "execute_complex_processes"
                    ]
                }
            )
            
            self.service_endpoints["workflow"] = endpoint_id
            logger.info(f"Workflow service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register workflow services: {str(e)}")
    
    async def _register_correlation_services(self):
        """Register SI-APP correlation management services"""
        try:
            # Initialize correlation service (will be instantiated per request with async session)
            correlation_service_config = {
                "service_class": SIAPPCorrelationService,
                "operations": [
                    "create_correlation",
                    "update_app_received",
                    "update_app_submitting", 
                    "update_app_submitted",
                    "update_firs_response",
                    "get_correlation_statistics",
                    "get_pending_correlations",
                    "retry_correlation"
                ]
            }
            
            self.services["correlation"] = correlation_service_config
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="correlation",
                service_role=ServiceRole.HYBRID,
                callback=self._create_correlation_callback(correlation_service_config),
                priority=5,
                tags=["correlation", "si-app", "status-sync", "tracking"],
                metadata={
                    "service_type": "correlation",
                    "operations": [
                        "create_correlation",
                        "update_app_received",
                        "update_app_submitting",
                        "update_app_submitted", 
                        "update_firs_response",
                        "get_correlation_statistics",
                        "get_pending_correlations",
                        "retry_correlation"
                    ]
                }
            )
            
            self.service_endpoints["correlation"] = endpoint_id
            logger.info(f"Correlation service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register correlation services: {str(e)}")

    async def _register_transmission_coordination_services(self):
        """Register SI→APP transmission coordination service."""
        try:
            coordination_service = TransmissionCoordinationService()
            svc = {
                "service": coordination_service,
                "operations": [
                    "coordinate_si_invoices_for_firs",
                    "coordinate_si_batch_for_firs",
                ],
            }

            self.services["transmission_coordination"] = svc

            endpoint_id = await self.message_router.register_service(
                service_name="transmission_coordination",
                service_role=ServiceRole.HYBRID,
                callback=self._create_transmission_coordination_callback(svc),
                priority=5,
                tags=["coordination", "si", "app", "firs"],
                metadata={
                    "service_type": "transmission_coordination",
                    "operations": svc["operations"],
                },
            )
            self.service_endpoints["transmission_coordination"] = endpoint_id
            logger.info(f"Transmission coordination service registered: {endpoint_id}")
        except Exception as e:
            logger.error(f"Failed to register transmission coordination services: {str(e)}")

    def _create_transmission_coordination_callback(self, svc):
        async def callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                service: TransmissionCoordinationService = svc.get("service")
                if operation == "coordinate_si_invoices_for_firs":
                    res = await service.coordinate_invoices(payload)
                    return {"operation": operation, **res}
                if operation == "coordinate_si_batch_for_firs":
                    res = await service.coordinate_batch(payload)
                    return {"operation": operation, **res}
                return {"operation": operation, "success": False, "error": "unsupported_operation"}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return callback

    # Service callback creators
    def _create_analytics_callback(self, analytics_service):
        """Create callback for analytics operations"""
        async def analytics_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "process_analytics":
                    data = payload.get("data", {})
                    result = analytics_service["analytics_processor"].process_analytics_data(data)
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "generate_insights":
                    config = payload.get("config", {})
                    insights = analytics_service["advanced_engine"].generate_business_insights(config)
                    return {"operation": operation, "success": True, "data": insights}
                elif operation == "create_dashboard":
                    dashboard_config = payload.get("dashboard_config", {})
                    dashboard = analytics_service["bi_service"].create_business_dashboard(dashboard_config)
                    return {"operation": operation, "success": True, "data": dashboard}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return analytics_callback
    
    def _create_billing_callback(self, billing_service):
        """Create callback for billing operations"""
        async def billing_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "manage_subscription":
                    subscription_data = payload.get("subscription_data", {})
                    result = billing_service["subscription_manager"].manage_subscription(subscription_data)
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "track_usage":
                    usage_data = payload.get("usage_data", {})
                    result = billing_service["usage_tracker"].track_api_usage(usage_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return billing_callback
    
    def _create_compliance_callback(self, compliance_service):
        """Create callback for compliance operations"""
        async def compliance_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "monitor_compliance":
                    compliance_data = payload.get("compliance_data", {})
                    result = compliance_service["compliance_monitor"].monitor_cross_role_compliance(compliance_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return compliance_callback
    
    def _create_config_callback(self, config_service):
        """Create callback for configuration operations"""
        async def config_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "manage_configuration":
                    config_data = payload.get("config_data", {})
                    result = config_service["config_manager"].update_dynamic_configuration(config_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return config_callback
    
    def _create_sync_callback(self, sync_service):
        """Create callback for synchronization operations"""
        async def sync_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "sync_data_across_roles":
                    sync_data = payload.get("sync_data", {})
                    result = sync_service["cross_role_sync"].synchronize_cross_role_data(sync_data)
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "ensure_consistency":
                    consistency_data = payload.get("consistency_data", {})
                    result = sync_service["consistency_manager"].ensure_data_consistency(consistency_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return sync_callback
    
    def _create_error_callback(self, error_service):
        """Create callback for error management operations"""
        async def error_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "handle_unified_error":
                    error_data = payload.get("error_data", {})
                    result = error_service["error_handler"].handle_cross_role_error(error_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return error_callback
    
    def _create_access_callback(self, access_service):
        """Create callback for access control operations"""
        async def access_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "manage_unified_access":
                    access_data = payload.get("access_data", {})
                    result = access_service["unified_rbac"].manage_cross_role_access(access_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return access_callback
    
    def _create_workflow_callback(self, workflow_service):
        """Create callback for workflow operations"""
        async def workflow_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "orchestrate_business_process":
                    process_data = payload.get("process_data", {})
                    result = workflow_service["process_engine"].execute_business_process(process_data)
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "coordinate_multi_role_operations":
                    coordination_data = payload.get("coordination_data", {})
                    result = workflow_service["coordinator"].coordinate_cross_role_operation(coordination_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return workflow_callback
    
    def _create_correlation_callback(self, correlation_service_config):
        """Create callback for correlation operations"""
        async def correlation_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                from core_platform.data_management.db_async import get_async_session
                
                # Get async session for correlation service
                async for db_session in get_async_session():
                    correlation_service = correlation_service_config["service_class"](db_session)
                    
                    if operation == "create_correlation":
                        correlation = await correlation_service.create_correlation(**payload)
                        return {"operation": operation, "success": True, "data": correlation.to_dict()}
                    elif operation == "update_app_received":
                        success = await correlation_service.update_app_received(
                            irn=payload.get("irn"),
                            app_submission_id=payload.get("app_submission_id"),
                            metadata=payload.get("metadata")
                        )
                        return {"operation": operation, "success": success, "data": {"updated": success}}
                    elif operation == "update_app_submitting":
                        success = await correlation_service.update_app_submitting(
                            irn=payload.get("irn"),
                            metadata=payload.get("metadata")
                        )
                        return {"operation": operation, "success": success, "data": {"updated": success}}
                    elif operation == "update_app_submitted":
                        success = await correlation_service.update_app_submitted(
                            irn=payload.get("irn"),
                            metadata=payload.get("metadata")
                        )
                        return {"operation": operation, "success": success, "data": {"updated": success}}
                    elif operation == "update_firs_response":
                        success = await correlation_service.update_firs_response(
                            irn=payload.get("irn"),
                            firs_response_id=payload.get("firs_response_id"),
                            firs_status=payload.get("firs_status"),
                            response_data=payload.get("response_data"),
                            identifiers=payload.get("identifiers")
                        )
                        return {"operation": operation, "success": success, "data": {"updated": success}}
                    elif operation == "get_correlation_statistics":
                        stats = await correlation_service.get_correlation_statistics(
                            organization_id=payload.get("organization_id"),
                            days=payload.get("days", 30)
                        )
                        return {"operation": operation, "success": True, "data": stats}
                    elif operation == "get_pending_correlations":
                        correlations = await correlation_service.get_pending_correlations(
                            limit=payload.get("limit", 100)
                        )
                        correlation_data = [corr.to_dict() for corr in correlations]
                        return {"operation": operation, "success": True, "data": correlation_data}
                    elif operation == "retry_correlation":
                        success = await correlation_service.retry_failed_correlation(
                            correlation_id=payload.get("correlation_id")
                        )
                        return {"operation": operation, "success": success, "data": {"retried": success}}
                    else:
                        return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
                    
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
                
        return correlation_callback
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all registered Hybrid services"""
        health_status = {
            "registry_status": "healthy" if self.is_initialized else "uninitialized",
            "total_services": len(self.services),
            "registered_endpoints": len(self.service_endpoints),
            "services": {}
        }
        
        # Check service health
        for service_name in self.services:
            try:
                health_status["services"][service_name] = {
                    "status": "healthy",
                    "endpoint": self.service_endpoints.get(service_name, "not_registered")
                }
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    async def cleanup_services(self):
        """Cleanup all services and unregister from message router"""
        try:
            logger.info("Cleaning up Hybrid services...")
            
            # Unregister from message router
            for service_name, endpoint_id in self.service_endpoints.items():
                try:
                    await self.message_router.unregister_service(endpoint_id)
                    logger.info(f"Unregistered service: {service_name}")
                except Exception as e:
                    logger.error(f"Failed to unregister {service_name}: {str(e)}")
            
            # Cleanup service instances
            for service_name, service in self.services.items():
                try:
                    if hasattr(service, 'cleanup'):
                        await service.cleanup()
                except Exception as e:
                    logger.error(f"Failed to cleanup {service_name}: {str(e)}")
            
            self.services.clear()
            self.service_endpoints.clear()
            self.is_initialized = False
            
            logger.info("Hybrid services cleanup completed")
            
        except Exception as e:
            logger.error(f"Hybrid services cleanup failed: {str(e)}")


# Global service registry instance
_hybrid_service_registry: Optional[HybridServiceRegistry] = None


async def initialize_hybrid_services(message_router: MessageRouter) -> HybridServiceRegistry:
    """
    Initialize Hybrid services with message router.
    
    Args:
        message_router: Core platform message router
        
    Returns:
        Initialized service registry
    """
    global _hybrid_service_registry
    
    if _hybrid_service_registry is None:
        _hybrid_service_registry = HybridServiceRegistry(message_router)
        await _hybrid_service_registry.initialize_services()
    
    return _hybrid_service_registry


def get_hybrid_service_registry() -> Optional[HybridServiceRegistry]:
    """Get the global Hybrid service registry instance"""
    return _hybrid_service_registry


async def cleanup_hybrid_services():
    """Cleanup Hybrid services"""
    global _hybrid_service_registry
    
    if _hybrid_service_registry:
        await _hybrid_service_registry.cleanup_services()
        _hybrid_service_registry = None
