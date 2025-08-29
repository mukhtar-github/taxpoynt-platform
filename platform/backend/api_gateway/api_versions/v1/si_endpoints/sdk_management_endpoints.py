"""
SDK Management Endpoints - API Version 1
========================================
Backend endpoints for System Integrator SDK management functionality.
Provides SDK generation, download, documentation, and testing capabilities.
"""

import logging
import os
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import HTTPBearer
import json

from core_platform.authentication.role_manager import PlatformRole, RoleScope
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.documentation.sdk_generator import SDKGenerator, SDKConfig, SDKLanguage
from ..version_models import V1ResponseModel, V1ErrorModel

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Mock SDK data for demonstration
MOCK_SDK_CATALOG = {
    "python": {
        "name": "Python SDK",
        "version": "1.0.0",
        "language": "python",
        "description": "Official Python SDK for TaxPoynt platform integration",
        "features": ["Authentication", "Invoice Management", "Compliance Checking", "Webhook Handling"],
        "download_count": 1250,
        "last_updated": "2024-12-31T00:00:00Z",
        "compatibility": ["Python 3.8+", "FastAPI", "Django", "Flask"],
        "documentation_url": "/api/v1/si/sdk/documentation/python",
        "examples": ["Basic Integration", "Invoice Creation", "Webhook Processing"],
        "dependencies": ["requests>=2.25.0", "pydantic>=1.8.0"]
    },
    "javascript": {
        "name": "JavaScript/Node.js SDK",
        "version": "1.0.0",
        "language": "javascript",
        "description": "Official JavaScript SDK for TaxPoynt platform integration",
        "features": ["Browser & Node.js Support", "TypeScript Types", "Promise-based API", "Error Handling"],
        "download_count": 890,
        "last_updated": "2024-12-31T00:00:00Z",
        "compatibility": ["Node.js 16+", "Modern Browsers", "React", "Vue.js"],
        "documentation_url": "/api/v1/si/sdk/documentation/javascript",
        "examples": ["Frontend Integration", "Backend API", "Webhook Endpoints"],
        "dependencies": ["axios>=0.21.0", "joi>=17.0.0"]
    }
}

# Mock API testing scenarios
MOCK_API_SCENARIOS = {
    "authentication": {
        "name": "Authentication Test",
        "description": "Test API key authentication and token generation",
        "endpoint": "/api/v1/auth/login",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": {"api_key": "your_api_key", "api_secret": "your_api_secret"},
        "expected_response": {"status": "success", "token": "jwt_token_here"}
    },
    "invoice_creation": {
        "name": "Invoice Creation Test",
        "description": "Test creating a new invoice through the API",
        "endpoint": "/api/v1/invoices",
        "method": "POST",
        "headers": {"Authorization": "Bearer {token}", "Content-Type": "application/json"},
        "body": {
            "invoice_number": "INV-001",
            "amount": 1000.00,
            "currency": "NGN",
            "customer_name": "Test Customer",
            "items": [{"name": "Test Item", "quantity": 1, "unit_price": 1000.00}]
        },
        "expected_response": {"status": "success", "invoice_id": "inv_123"}
    }
}

def create_sdk_management_router(role_detector, permission_guard: APIPermissionGuard, message_router: MessageRouter) -> APIRouter:
    """Create SDK management router with all endpoints"""
    
    router = APIRouter(prefix="/sdk", tags=["SDK Management"])
    
    @router.get("/catalog", response_model=V1ResponseModel)
    async def get_sdk_catalog(
        request: Request,
        language: Optional[str] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Get available SDKs catalog with optional language filtering"""
        try:
            catalog = MOCK_SDK_CATALOG
            
            if language:
                catalog = {k: v for k, v in catalog.items() if v["language"] == language}
            
            return V1ResponseModel(
                success=True,
                data={
                    "sdk_catalog": catalog,
                    "total_count": len(catalog),
                    "languages_available": list(set(sdk["language"] for sdk in catalog.values()))
                },
                message="SDK catalog retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve SDK catalog: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve SDK catalog")
    
    @router.get("/catalog/{language}", response_model=V1ResponseModel)
    async def get_sdk_by_language(
        language: str,
        request: Request,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Get specific SDK by programming language"""
        try:
            if language not in MOCK_SDK_CATALOG:
                raise HTTPException(status_code=404, detail=f"SDK for language '{language}' not found")
            
            sdk_info = MOCK_SDK_CATALOG[language]
            
            return V1ResponseModel(
                success=True,
                data={"sdk": sdk_info},
                message=f"SDK for {language} retrieved successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve SDK for {language}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve SDK information")
    
    @router.post("/generate", response_model=V1ResponseModel)
    async def generate_sdk(
        request: Request,
        sdk_config: SDKConfig,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Generate a new SDK based on configuration"""
        try:
            # Initialize SDK generator
            generator = SDKGenerator()
            
            # Generate SDK
            sdk_path = await generator.generate_sdk(sdk_config)
            
            if not sdk_path or not sdk_path.exists():
                raise HTTPException(status_code=500, detail="SDK generation failed")
            
            # Log SDK generation
            logger.info(f"SDK generated successfully for {sdk_config.language} at {sdk_path}")
            
            return V1ResponseModel(
                success=True,
                data={
                    "sdk_path": str(sdk_path),
                    "language": sdk_config.language.value,
                    "generated_at": datetime.utcnow().isoformat(),
                    "download_url": f"/api/v1/si/sdk/download/{sdk_path.name}"
                },
                message="SDK generated successfully"
            )
            
        except Exception as e:
            logger.error(f"SDK generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"SDK generation failed: {str(e)}")
    
    @router.get("/download/{sdk_name}")
    async def download_sdk(
        sdk_name: str,
        request: Request,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Download generated SDK as ZIP file"""
        try:
            # Create temporary directory and mock SDK files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create mock SDK structure
                sdk_dir = temp_path / sdk_name
                sdk_dir.mkdir()
                
                # Create README
                readme_content = f"""# TaxPoynt {sdk_name.upper()} SDK
                
Generated on: {datetime.utcnow().isoformat()}

## Installation
```bash
pip install taxpoynt-{sdk_name.lower()}
```

## Quick Start
```python
from taxpoynt import TaxPoyntClient

client = TaxPoyntClient(api_key="your_api_key")
# Your integration code here
```
"""
                
                with open(sdk_dir / "README.md", "w") as f:
                    f.write(readme_content)
                
                # Create main SDK file
                sdk_content = f"""# TaxPoynt {sdk_name.upper()} SDK
import requests
import json

class TaxPoyntClient:
    def __init__(self, api_key: str, base_url: str = "https://api.taxpoynt.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({{
            "Authorization": f"Bearer {{api_key}}",
            "Content-Type": "application/json"
        }})
    
    def create_invoice(self, invoice_data: dict):
        response = self.session.post(f"{{self.base_url}}/api/v1/invoices", json=invoice_data)
        return response.json()
    
    def get_invoice(self, invoice_id: str):
        response = self.session.get(f"{{self.base_url}}/api/v1/invoices/{{invoice_id}}")
        return response.json()
"""
                
                with open(sdk_dir / f"taxpoynt_{sdk_name.lower()}.py", "w") as f:
                    f.write(sdk_content)
                
                # Create requirements.txt
                requirements_content = """requests>=2.25.0
pydantic>=1.8.0
python-dotenv>=0.19.0
"""
                
                with open(sdk_dir / "requirements.txt", "w") as f:
                    f.write(requirements_content)
                
                # Create ZIP file
                zip_path = temp_path / f"{sdk_name}_sdk.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in sdk_dir.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(sdk_dir)
                            zipf.write(file_path, arcname)
                
                # Return ZIP file as download
                return FileResponse(
                    path=str(zip_path),
                    filename=f"{sdk_name}_sdk.zip",
                    media_type="application/zip"
                )
                
        except Exception as e:
            logger.error(f"SDK download failed: {e}")
            raise HTTPException(status_code=500, detail="SDK download failed")
    
    @router.get("/documentation/{language}", response_model=V1ResponseModel)
    async def get_sdk_documentation(
        language: str,
        request: Request,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Get comprehensive SDK documentation for a specific language"""
        try:
            if language not in MOCK_SDK_CATALOG:
                raise HTTPException(status_code=404, detail=f"Documentation for language '{language}' not found")
            
            # Mock documentation content
            documentation = {
                "overview": {
                    "title": f"TaxPoynt {language.upper()} SDK Overview",
                    "description": f"Complete integration guide for the {language.upper()} SDK",
                    "version": "1.0.0",
                    "last_updated": "2024-12-31"
                },
                "quick_start": {
                    "title": "Quick Start Guide",
                    "steps": [
                        "Install the SDK",
                        "Configure your API credentials",
                        "Create your first invoice",
                        "Handle webhooks"
                    ],
                    "code_examples": {
                        "installation": f"npm install @taxpoynt/{language}-sdk",
                        "basic_usage": f"const client = new TaxPoyntClient('your_api_key');"
                    }
                },
                "api_reference": {
                    "title": "API Reference",
                    "endpoints": [
                        {"name": "Authentication", "method": "POST", "path": "/auth/login"},
                        {"name": "Create Invoice", "method": "POST", "path": "/invoices"},
                        {"name": "Get Invoice", "method": "GET", "path": "/invoices/{id}"},
                        {"name": "Webhook Handler", "method": "POST", "path": "/webhooks"}
                    ]
                },
                "examples": {
                    "title": "Code Examples",
                    "snippets": [
                        {"name": "Basic Integration", "code": "// Basic integration example"},
                        {"name": "Invoice Creation", "code": "// Invoice creation example"},
                        {"name": "Error Handling", "code": "// Error handling example"}
                    ]
                },
                "troubleshooting": {
                    "title": "Troubleshooting",
                    "common_issues": [
                        "Authentication errors",
                        "Rate limiting",
                        "Webhook delivery issues"
                    ]
                }
            }
            
            return V1ResponseModel(
                success=True,
                data={"documentation": documentation},
                message=f"Documentation for {language} retrieved successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve documentation for {language}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve documentation")
    
    @router.get("/sandbox/scenarios", response_model=V1ResponseModel)
    async def get_sandbox_scenarios(
        request: Request,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Get available API testing scenarios for sandbox"""
        try:
            return V1ResponseModel(
                success=True,
                data={"scenarios": MOCK_API_SCENARIOS},
                message="Sandbox scenarios retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve sandbox scenarios: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve sandbox scenarios")
    
    @router.post("/sandbox/test", response_model=V1ResponseModel)
    async def test_api_scenario(
        request: Request,
        scenario_name: str,
        api_key: str,
        custom_headers: Optional[Dict[str, str]] = None,
        custom_body: Optional[Dict[str, Any]] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Test an API scenario in the sandbox environment"""
        try:
            if scenario_name not in MOCK_API_SCENARIOS:
                raise HTTPException(status_code=404, detail=f"Scenario '{scenario_name}' not found")
            
            scenario = MOCK_API_SCENARIOS[scenario_name]
            
            # In production, this would make actual API calls to test endpoints
            # For now, we'll simulate the response
            
            # Simulate API call delay
            import asyncio
            await asyncio.sleep(0.5)
            
            # Mock successful response
            test_result = {
                "scenario": scenario_name,
                "status": "success",
                "response_time_ms": 450,
                "status_code": 200,
                "response_body": scenario["expected_response"],
                "headers_sent": {**scenario["headers"], **(custom_headers or {})},
                "body_sent": custom_body or scenario["body"],
                "tested_at": datetime.utcnow().isoformat()
            }
            
            # Log the test
            logger.info(f"API scenario '{scenario_name}' tested successfully by user")
            
            return V1ResponseModel(
                success=True,
                data={"test_result": test_result},
                message="API scenario tested successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API scenario test failed: {e}")
            raise HTTPException(status_code=500, detail="API scenario test failed")
    
    @router.get("/analytics/usage", response_model=V1ResponseModel)
    async def get_sdk_usage_analytics(
        request: Request,
        period: str = "30d",
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Get SDK usage analytics and metrics"""
        try:
            # Mock analytics data
            analytics = {
                "period": period,
                "total_downloads": sum(sdk["download_count"] for sdk in MOCK_SDK_CATALOG.values()),
                "downloads_by_language": {lang: sdk["download_count"] for lang, sdk in MOCK_SDK_CATALOG.items()},
                "popular_features": ["Authentication", "Invoice Management", "Compliance Checking"],
                "integration_success_rate": 0.94,
                "average_response_time_ms": 245,
                "error_rate": 0.06,
                "top_organizations": ["TechCorp", "FinanceHub", "RetailPlus"],
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return V1ResponseModel(
                success=True,
                data={"analytics": analytics},
                message="SDK usage analytics retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve SDK analytics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve analytics")
    
    @router.post("/feedback", response_model=V1ResponseModel)
    async def submit_sdk_feedback(
        request: Request,
        language: str,
        feedback_type: str,
        rating: int,
        comments: Optional[str] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE))
    ):
        """Submit feedback for SDK experience"""
        try:
            if language not in MOCK_SDK_CATALOG:
                raise HTTPException(status_code=404, detail=f"Language '{language}' not found")
            
            if not 1 <= rating <= 5:
                raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
            
            # In production, this would save to database
            feedback = {
                "language": language,
                "feedback_type": feedback_type,
                "rating": rating,
                "comments": comments,
                "submitted_at": datetime.utcnow().isoformat(),
                "user_id": context.user_id if context else "anonymous"
            }
            
            # Log feedback
            logger.info(f"SDK feedback submitted for {language}: {rating}/5 - {feedback_type}")
            
            return V1ResponseModel(
                success=True,
                data={"feedback": feedback},
                message="Feedback submitted successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit feedback")
    
    return router
