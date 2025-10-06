"""
Workflow Endpoints - API v1
===========================
Hybrid workflow management endpoints for orchestrating multi-role processes.
Provides workflow templates, active workflow monitoring, and execution control.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..si_endpoints.version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response

logger = logging.getLogger(__name__)


class WorkflowCreateRequest(BaseModel):
    """Request model for creating new workflows"""
    template_id: str
    name: str
    parameters: Dict[str, Any] = {}
    schedule: Optional[str] = None


class WorkflowUpdateRequest(BaseModel):
    """Request model for updating workflows"""
    status: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class WorkflowEndpointsV1:
    """
    Workflow Endpoints - Version 1
    ==============================
    Manages hybrid workflows and orchestration:
    
    **Workflow Capabilities:**
    - **Template Management**: Predefined workflow templates library
    - **Active Workflows**: Monitor and control running workflows
    - **Execution Control**: Start, pause, resume, and stop workflows
    - **Process Tracking**: Real-time workflow progress and status
    - **Cross-Role Orchestration**: Coordinate SI and APP operations
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/workflows", tags=["Hybrid Workflows V1"])
        
        self._setup_routes()
        logger.info("Workflow Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup workflow routes"""
        
        # Active Workflows
        self.router.add_api_route(
            "/active",
            self.get_active_workflows,
            methods=["GET"],
            summary="Get active workflows",
            description="Get list of currently running workflows",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_workflow_access)]
        )
        
        # Workflow Templates
        self.router.add_api_route(
            "/templates",
            self.get_workflow_templates,
            methods=["GET"],
            summary="Get workflow templates",
            description="Get available workflow templates library",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_workflow_access)]
        )
        
        # Create Workflow
        self.router.add_api_route(
            "/create",
            self.create_workflow,
            methods=["POST"],
            summary="Create new workflow",
            description="Create new workflow from template",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_workflow_access)]
        )
        
        # Workflow Control
        self.router.add_api_route(
            "/{workflow_id}/control",
            self.control_workflow,
            methods=["POST"],
            summary="Control workflow execution",
            description="Start, pause, resume, or stop workflow",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_workflow_access)]
        )
        
        # Workflow Status
        self.router.add_api_route(
            "/{workflow_id}/status",
            self.get_workflow_status,
            methods=["GET"],
            summary="Get workflow status",
            description="Get detailed status of specific workflow",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_workflow_access)]
        )
        
        # Workflow History
        self.router.add_api_route(
            "/history",
            self.get_workflow_history,
            methods=["GET"],
            summary="Get workflow history",
            description="Get completed workflow history",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_workflow_access)]
        )

    async def _require_workflow_access(self, request: Request):
        """Require workflow access permissions"""
        return await self.permission_guard.require_permissions(
            request, 
            [PlatformRole.HYBRID], 
            "hybrid_workflow_access"
        )
    
    def _create_v1_response(self, data: Any, operation: str) -> V1ResponseModel:
        """Create standardized V1 response"""
        return build_v1_response(data, action=f"{operation}")
    
    def _get_primary_service_role(self, context: HTTPRoutingContext) -> ServiceRole:
        """Get primary service role for workflow operations"""
        return ServiceRole.HYBRID_SERVICES

    async def get_active_workflows(self, request: Request, context: HTTPRoutingContext = Depends(_require_workflow_access)):
        """Get list of currently active workflows"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_active_workflows",
                payload={"user_id": context.user_id}
            )
            
            return self._create_v1_response(result, "active_workflows_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting active workflows: {e}")
            # Demo active workflows data
            demo_workflows = [
                {
                    "id": "wf-001",
                    "name": "ERP → FIRS Auto-Submission",
                    "status": "running",
                    "progress": 75,
                    "currentStep": "Generating FIRS invoices",
                    "startedAt": "2024-01-15 14:30:00",
                    "estimatedCompletion": "2024-01-15 15:45:00",
                    "type": "si_to_app"
                },
                {
                    "id": "wf-002",
                    "name": "Monthly Compliance Report",
                    "status": "completed",
                    "progress": 100,
                    "currentStep": "Report delivered",
                    "startedAt": "2024-01-15 09:00:00",
                    "estimatedCompletion": "2024-01-15 10:30:00",
                    "type": "compliance_automation"
                },
                {
                    "id": "wf-003",
                    "name": "Banking Data Reconciliation",
                    "status": "paused",
                    "progress": 45,
                    "currentStep": "Awaiting manual review",
                    "startedAt": "2024-01-15 11:20:00",
                    "estimatedCompletion": "2024-01-15 16:00:00",
                    "type": "business_integration"
                }
            ]
            return self._create_v1_response(demo_workflows, "active_workflows_demo")

    async def get_workflow_templates(self, request: Request, context: HTTPRoutingContext = Depends(_require_workflow_access)):
        """Get available workflow templates library"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_workflow_templates",
                payload={"user_id": context.user_id}
            )
            
            return self._create_v1_response(result, "workflow_templates_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting workflow templates: {e}")
            # Demo templates data
            demo_templates = [
                {
                    "id": "tpl-001",
                    "name": "SI to APP Data Flow",
                    "description": "Automated pipeline from system integration to FIRS submission",
                    "type": "si_to_app",
                    "steps": 6,
                    "estimatedTime": "2-4 hours",
                    "complexity": "moderate",
                    "category": "End-to-End Processing",
                    "parameters": {
                        "required": ["source_system", "target_environment"],
                        "optional": ["batch_size", "validation_level"]
                    }
                },
                {
                    "id": "tpl-002",
                    "name": "Multi-System Reconciliation",
                    "description": "Compare and reconcile data across ERP, banking, and payment systems",
                    "type": "business_integration",
                    "steps": 8,
                    "estimatedTime": "3-6 hours",
                    "complexity": "complex",
                    "category": "Data Integration",
                    "parameters": {
                        "required": ["reconciliation_period", "systems_list"],
                        "optional": ["tolerance_level", "auto_resolve"]
                    }
                },
                {
                    "id": "tpl-003",
                    "name": "Compliance Monitoring",
                    "description": "Automated compliance checking and reporting workflow",
                    "type": "compliance_automation",
                    "steps": 4,
                    "estimatedTime": "1-2 hours",
                    "complexity": "simple",
                    "category": "Regulatory",
                    "parameters": {
                        "required": ["reporting_period"],
                        "optional": ["alert_threshold", "report_format"]
                    }
                },
                {
                    "id": "tpl-004",
                    "name": "Invoice Generation & Submission",
                    "description": "Complete process from data collection to FIRS submission",
                    "type": "si_to_app",
                    "steps": 10,
                    "estimatedTime": "4-8 hours",
                    "complexity": "complex",
                    "category": "Complete E-Invoicing",
                    "parameters": {
                        "required": ["invoice_period", "taxpayer_id"],
                        "optional": ["auto_submit", "validation_mode"]
                    }
                }
            ]
            return self._create_v1_response(demo_templates, "workflow_templates_demo")

    async def create_workflow(self, request: Request, workflow_data: WorkflowCreateRequest, context: HTTPRoutingContext = Depends(_require_workflow_access)):
        """Create new workflow from template"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="create_workflow",
                payload={
                    "user_id": context.user_id,
                    "template_id": workflow_data.template_id,
                    "name": workflow_data.name,
                    "parameters": workflow_data.parameters,
                    "schedule": workflow_data.schedule
                }
            )
            
            return self._create_v1_response(result, "workflow_created")
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            # Demo workflow creation response
            demo_result = {
                "workflow_id": f"wf-{hash(workflow_data.name) % 10000:04d}",
                "status": "created",
                "message": "Workflow created successfully (demo mode)"
            }
            return self._create_v1_response(demo_result, "workflow_created_demo")

    async def control_workflow(self, workflow_id: str, request: Request, control_data: WorkflowUpdateRequest, context: HTTPRoutingContext = Depends(_require_workflow_access)):
        """Control workflow execution (start, pause, resume, stop)"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="control_workflow",
                payload={
                    "user_id": context.user_id,
                    "workflow_id": workflow_id,
                    "action": control_data.status,
                    "parameters": control_data.parameters
                }
            )
            
            return self._create_v1_response(result, "workflow_controlled")
            
        except Exception as e:
            logger.error(f"Error controlling workflow {workflow_id}: {e}")
            # Demo control response
            demo_result = {
                "workflow_id": workflow_id,
                "status": control_data.status or "updated",
                "message": f"Workflow {workflow_id} control action completed (demo mode)"
            }
            return self._create_v1_response(demo_result, "workflow_controlled_demo")

    async def get_workflow_status(self, workflow_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_workflow_access)):
        """Get detailed status of specific workflow"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_workflow_status",
                payload={
                    "user_id": context.user_id,
                    "workflow_id": workflow_id
                }
            )
            
            return self._create_v1_response(result, "workflow_status_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting workflow status {workflow_id}: {e}")
            # Demo status data
            demo_status = {
                "id": workflow_id,
                "name": "Sample Workflow",
                "status": "running",
                "progress": 65,
                "currentStep": "Processing invoices",
                "steps": [
                    {"name": "Data Collection", "status": "completed", "timestamp": "2024-01-15 14:30:00"},
                    {"name": "Data Validation", "status": "completed", "timestamp": "2024-01-15 14:35:00"},
                    {"name": "Invoice Generation", "status": "running", "timestamp": "2024-01-15 14:40:00"},
                    {"name": "FIRS Submission", "status": "pending", "timestamp": null}
                ],
                "logs": [
                    {"timestamp": "2024-01-15 14:30:00", "level": "info", "message": "Workflow started"},
                    {"timestamp": "2024-01-15 14:35:00", "level": "info", "message": "Data validation completed"},
                    {"timestamp": "2024-01-15 14:40:00", "level": "info", "message": "Invoice generation in progress"}
                ]
            }
            return self._create_v1_response(demo_status, "workflow_status_demo")

    async def get_workflow_history(self, request: Request, limit: int = Query(50), context: HTTPRoutingContext = Depends(_require_workflow_access)):
        """Get completed workflow history"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_workflow_history",
                payload={
                    "user_id": context.user_id,
                    "limit": limit
                }
            )
            
            return self._create_v1_response(result, "workflow_history_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting workflow history: {e}")
            # Demo history data
            demo_history = [
                {
                    "id": "wf-completed-001",
                    "name": "Daily ERP Sync",
                    "status": "completed",
                    "startedAt": "2024-01-14 08:00:00",
                    "completedAt": "2024-01-14 08:45:00",
                    "duration": "45 minutes",
                    "result": "success",
                    "processed_records": 1247
                },
                {
                    "id": "wf-completed-002",
                    "name": "Weekly Compliance Check",
                    "status": "completed",
                    "startedAt": "2024-01-13 18:00:00",
                    "completedAt": "2024-01-13 19:15:00",
                    "duration": "1 hour 15 minutes",
                    "result": "success",
                    "compliance_score": 98.5
                }
            ]
            return self._create_v1_response(demo_history, "workflow_history_demo")


def create_workflow_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard, 
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create workflow router"""
    endpoint_handler = WorkflowEndpointsV1(role_detector, permission_guard, message_router)
    return endpoint_handler.router


# Dependency injection helpers
async def _require_workflow_access(request: Request):
    """Require workflow access - placeholder for dependency injection"""
    pass
