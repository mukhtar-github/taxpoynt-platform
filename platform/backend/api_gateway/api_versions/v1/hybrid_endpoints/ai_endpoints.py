"""
AI Service Endpoints - Hybrid API v1
====================================
REST API endpoints for AI service capabilities including
insights generation, trend analysis, and data classification.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from pydantic import BaseModel, Field
from uuid import UUID

from core_platform.ai import AIService, get_ai_service, AIConfig, AICapability
from core_platform.authentication.role_manager import PlatformRole, RoleScope
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..si_endpoints.version_models import V1ResponseModel, V1ErrorModel

logger = logging.getLogger(__name__)


# Request/Response Models
class InsightGenerationRequest(BaseModel):
    """Request model for insight generation"""
    data: Dict[str, Any] = Field(..., description="Input data for insight generation")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    capabilities: Optional[List[str]] = Field(None, description="Specific AI capabilities to use")
    
    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "metrics": {"revenue": 150000, "transactions": 1250},
                    "kpis": {"conversion_rate": 0.85, "customer_satisfaction": 4.2},
                    "trends": {"growth_rate": 0.15, "seasonality": "high"}
                },
                "context": {"time_period": "last_30_days", "business_unit": "e-invoicing"},
                "capabilities": ["insight_generation", "trend_analysis"]
            }
        }


class InsightGenerationResponse(BaseModel):
    """Response model for insight generation"""
    insights: List[Dict[str, Any]] = Field(..., description="Generated insights")
    metadata: Dict[str, Any] = Field(..., description="Generation metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "insights": [
                    {
                        "title": "Revenue Growth Trend",
                        "description": "Strong revenue growth of 15% detected",
                        "type": "performance",
                        "confidence": 0.92,
                        "recommendations": ["Maintain current strategies", "Scale operations"]
                    }
                ],
                "metadata": {
                    "generation_time": "2024-01-15T10:30:00Z",
                    "model": "taxpoynt-ai-v1",
                    "confidence_avg": 0.92
                }
            }
        }


class AnomalyDetectionRequest(BaseModel):
    """Request model for anomaly detection"""
    data: Dict[str, Any] = Field(..., description="Data to analyze for anomalies")
    sensitivity: Optional[float] = Field(0.5, description="Detection sensitivity (0.0-1.0)")
    
    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "time_series": [100, 105, 98, 102, 350, 99, 101],
                    "metrics": {"avg_response_time": 250, "error_rate": 0.02}
                },
                "sensitivity": 0.7
            }
        }


class ClassificationRequest(BaseModel):
    """Request model for data classification"""
    data: Any = Field(..., description="Data to classify")
    categories: List[str] = Field(..., description="Available categories")
    
    class Config:
        schema_extra = {
            "example": {
                "data": "Invoice processing error due to invalid VAT number format",
                "categories": ["technical_error", "business_rule_violation", "data_quality_issue"]
            }
        }


class SummarizationRequest(BaseModel):
    """Request model for text summarization"""
    text: str = Field(..., description="Text to summarize")
    max_length: Optional[int] = Field(200, description="Maximum summary length")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Long detailed report about e-invoice processing performance...",
                "max_length": 150
            }
        }


class AIHealthResponse(BaseModel):
    """AI service health status"""
    status: str = Field(..., description="Service status")
    provider: str = Field(..., description="AI provider")
    capabilities: List[str] = Field(..., description="Available capabilities")
    is_initialized: bool = Field(..., description="Initialization status")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "provider": "mock",
                "capabilities": ["insight_generation", "trend_analysis", "anomaly_detection"],
                "is_initialized": True
            }
        }


def create_ai_router(
    ai_service: AIService = None,
    permission_guard: APIPermissionGuard = None
) -> APIRouter:
    """
    Create AI endpoints router for hybrid services.
    
    Args:
        ai_service: AI service instance
        permission_guard: Permission guard for role-based access
        
    Returns:
        Configured APIRouter
    """
    router = APIRouter(prefix="/ai", tags=["AI Services"])
    
    # Dependency injection
    def get_ai_service_dep() -> AIService:
        if ai_service:
            return ai_service
        return get_ai_service()
    
    def get_permission_guard_dep() -> APIPermissionGuard:
        if permission_guard:
            return permission_guard
        # Return a basic permission guard if none provided
        return APIPermissionGuard()
    
    @router.get(
        "/health",
        response_model=V1ResponseModel[AIHealthResponse],
        summary="AI Service Health Check",
        description="Get AI service health status and capabilities"
    )
    async def ai_health_check(
        ai_svc: AIService = Depends(get_ai_service_dep)
    ):
        """Get AI service health and status."""
        try:
            health_data = await ai_svc.health_check()
            
            response_data = AIHealthResponse(
                status=health_data.get("status", "unknown"),
                provider=health_data.get("provider", "unknown"),
                capabilities=health_data.get("capabilities", []),
                is_initialized=health_data.get("is_initialized", False)
            )
            
            return V1ResponseModel(
                success=True,
                data=response_data,
                message="AI service health retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"AI health check failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI service health check failed: {str(e)}"
            )
    
    @router.post(
        "/insights/generate",
        response_model=V1ResponseModel[InsightGenerationResponse],
        summary="Generate Business Insights",
        description="Generate AI-powered business insights from provided data"
    )
    async def generate_insights(
        request: InsightGenerationRequest,
        background_tasks: BackgroundTasks,
        ai_svc: AIService = Depends(get_ai_service_dep),
        guard: APIPermissionGuard = Depends(get_permission_guard_dep)
    ):
        """Generate business insights using AI."""
        try:
            # Check AI service availability
            if not ai_svc.is_available():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service is not available"
                )
            
            # Generate insights
            result = await ai_svc.generate_insights(request.data)
            
            response_data = InsightGenerationResponse(
                insights=result.get("insights", []),
                metadata=result.get("metadata", {})
            )
            
            # Log insight generation for analytics
            background_tasks.add_task(
                _log_ai_operation,
                "insight_generation",
                len(result.get("insights", [])),
                request.data
            )
            
            return V1ResponseModel(
                success=True,
                data=response_data,
                message=f"Generated {len(result.get('insights', []))} insights successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Insight generation failed: {str(e)}"
            )
    
    @router.post(
        "/anomalies/detect",
        response_model=V1ResponseModel[Dict[str, Any]],
        summary="Detect Anomalies",
        description="Detect anomalies in provided data using AI"
    )
    async def detect_anomalies(
        request: AnomalyDetectionRequest,
        ai_svc: AIService = Depends(get_ai_service_dep)
    ):
        """Detect anomalies in data."""
        try:
            if not ai_svc.is_available():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service is not available"
                )
            
            result = await ai_svc.detect_anomalies(request.data)
            
            return V1ResponseModel(
                success=True,
                data=result,
                message="Anomaly detection completed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Anomaly detection failed: {str(e)}"
            )
    
    @router.post(
        "/trends/analyze",
        response_model=V1ResponseModel[Dict[str, Any]],
        summary="Analyze Trends",
        description="Analyze trends in provided data using AI"
    )
    async def analyze_trends(
        data: Dict[str, Any],
        ai_svc: AIService = Depends(get_ai_service_dep)
    ):
        """Analyze trends in data."""
        try:
            if not ai_svc.is_available():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service is not available"
                )
            
            result = await ai_svc.analyze_trends(data)
            
            return V1ResponseModel(
                success=True,
                data=result,
                message="Trend analysis completed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Trend analysis failed: {str(e)}"
            )
    
    @router.post(
        "/classify",
        response_model=V1ResponseModel[Dict[str, Any]],
        summary="Classify Data",
        description="Classify data into provided categories using AI"
    )
    async def classify_data(
        request: ClassificationRequest,
        ai_svc: AIService = Depends(get_ai_service_dep)
    ):
        """Classify data into categories."""
        try:
            if not ai_svc.is_available():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service is not available"
                )
            
            result = await ai_svc.classify_data(request.data, request.categories)
            
            return V1ResponseModel(
                success=True,
                data=result,
                message="Data classification completed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Data classification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Data classification failed: {str(e)}"
            )
    
    @router.post(
        "/summarize",
        response_model=V1ResponseModel[Dict[str, Any]],
        summary="Summarize Text",
        description="Summarize provided text using AI"
    )
    async def summarize_text(
        request: SummarizationRequest,
        ai_svc: AIService = Depends(get_ai_service_dep)
    ):
        """Summarize text content."""
        try:
            if not ai_svc.is_available():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="AI service is not available"
                )
            
            result = await ai_svc.summarize_text(request.text, request.max_length)
            
            return V1ResponseModel(
                success=True,
                data=result,
                message="Text summarization completed successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Text summarization failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Text summarization failed: {str(e)}"
            )
    
    return router


async def _log_ai_operation(operation_type: str, result_count: int, input_data: Dict[str, Any]):
    """Log AI operation for analytics (background task)."""
    try:
        logger.info(f"AI operation: {operation_type}, results: {result_count}, data_size: {len(str(input_data))}")
        # Could send to analytics service, metrics collector, etc.
    except Exception as e:
        logger.error(f"Failed to log AI operation: {e}")


# Export the router factory
__all__ = ["create_ai_router"]