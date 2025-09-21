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
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, HTTPException, Depends, status, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.security import HTTPBearer
import json

from core_platform.authentication.role_manager import PlatformRole, RoleScope
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.documentation.sdk_generator import SDKGenerator, SDKConfig, SDKLanguage
from core_platform.data_management.models import (
    SDK, SDKVersion, SDKDownload, SDKUsageLog, SandboxScenario, 
    SandboxTestResult, SDKDocumentation, SDKFeedback, SDKAnalytics,
    SDKLanguage as SDKLanguageEnum, SDKStatus, FeedbackType, TestStatus,
    DEMO_SDK_DATA, DEMO_SCENARIOS
)
from core_platform.services.sdk_management_service import SDKManagementService
from core_platform.data_management.db_async import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.idempotency.store import IdempotencyStore
from ..version_models import V1ResponseModel, V1ErrorModel  # pyright: ignore[reportMissingImports]

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Use imported demo data from models
MOCK_SDK_CATALOG = DEMO_SDK_DATA

# Use imported demo scenarios from models
MOCK_API_SCENARIOS = DEMO_SCENARIOS

def create_sdk_management_router(role_detector, permission_guard: APIPermissionGuard, message_router: MessageRouter) -> APIRouter:
    """Create SDK management router with all endpoints"""
    
    router = APIRouter(prefix="/sdk", tags=["SDK Management"])
    
    @router.get("/catalog", response_model=V1ResponseModel)
    async def get_sdk_catalog(
        request: Request,
        language: Optional[str] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db = Depends(get_async_session),
    ):
        """Get available SDKs catalog with optional language filtering"""
        try:
            sdk_service = SDKManagementService(db)
            catalog_data = await sdk_service.get_sdk_catalog(language)
            
            return V1ResponseModel(
                success=True,
                data=catalog_data,
                message="SDK catalog retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve SDK catalog: {e}")
            raise HTTPException(status_code=502, detail="Failed to retrieve SDK catalog")
    
    @router.get("/catalog/{language}", response_model=V1ResponseModel)
    async def get_sdk_by_language(
        language: str,
        request: Request,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db = Depends(get_async_session),
    ):
        """Get specific SDK by programming language"""
        try:
            sdk_service = SDKManagementService(db)
            sdk_info = await sdk_service.get_sdk_by_language(language)
            
            if not sdk_info:
                raise HTTPException(status_code=404, detail=f"SDK for language '{language}' not found")
            
            return V1ResponseModel(
                success=True,
                data={"sdk": sdk_info},
                message=f"SDK for {language} retrieved successfully"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve SDK for {language}: {e}")
            raise HTTPException(status_code=502, detail="Failed to retrieve SDK information")
    
    @router.post("/generate", response_model=V1ResponseModel)
    async def generate_sdk(
        request: Request,
        language: str,
        custom_config: Optional[Dict[str, Any]] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db: AsyncSession = Depends(get_async_session),
    ):
        """Generate a new SDK based on configuration"""
        try:
            body = {"language": language, "custom_config": custom_config or {}}
            # Idempotency
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(body)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(context.user_id) if context and getattr(context, 'user_id', None) else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return V1ResponseModel(success=True, data=stored, message="SDK generated successfully")

            sdk_service = SDKManagementService(db)
            sdk_data = await sdk_service.generate_sdk_package(language, custom_config)
            
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and getattr(context, 'user_id', None) else None,
                    key=idem_key,
                    response=sdk_data if isinstance(sdk_data, dict) else {"sdk": sdk_data},
                    status_code=200,
                )

            return V1ResponseModel(
                success=True,
                data=sdk_data,
                message="SDK generated successfully"
            )
            
        except Exception as e:
            logger.error(f"SDK generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"SDK generation failed: {str(e)}")
    
    @router.get("/download/{sdk_name}")
    async def download_sdk(
        sdk_name: str,
        request: Request,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db = Depends(get_async_session),
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
                    "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d")
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
            raise HTTPException(status_code=502, detail="Failed to retrieve documentation")
    
    @router.get("/sandbox/scenarios", response_model=V1ResponseModel)
    async def get_sandbox_scenarios(
        request: Request,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db = Depends(get_async_session),
    ):
        """Get available API testing scenarios for sandbox"""
        try:
            sdk_service = SDKManagementService(db)
            scenarios_data = await sdk_service.get_sandbox_scenarios()
            
            return V1ResponseModel(
                success=True,
                data=scenarios_data,
                message="Sandbox scenarios retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve sandbox scenarios: {e}")
            raise HTTPException(status_code=502, detail="Failed to retrieve sandbox scenarios")
    
    @router.post("/sandbox/test", response_model=V1ResponseModel)
    async def test_api_scenario(
        request: Request,
        scenario_name: str,
        api_key: str,
        custom_headers: Optional[Dict[str, str]] = None,
        custom_body: Optional[Dict[str, Any]] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db = Depends(get_async_session),
    ):
        """Test an API scenario in the sandbox environment"""
        try:
            sdk_service = SDKManagementService(db)
            
            test_data = {
                "api_key": api_key,
                "custom_headers": custom_headers or {},
                "custom_body": custom_body
            }
            
            user_id = getattr(context, 'user_id', 'anonymous')
            organization_id = getattr(context, 'organization_id', 'default')
            
            test_result = await sdk_service.execute_sandbox_test(
                scenario_name, user_id, organization_id, test_data
            )
            
            return V1ResponseModel(
                success=True,
                data={"test_result": test_result},
                message="API scenario tested successfully"
            )
            
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception as e:
            logger.error(f"API scenario test failed: {e}")
            raise HTTPException(status_code=500, detail="API scenario test failed")
    
    @router.get("/analytics/usage", response_model=V1ResponseModel)
    async def get_sdk_usage_analytics(
        request: Request,
        period: str = "30d",
        language: Optional[str] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db = Depends(get_async_session),
    ):
        """Get SDK usage analytics and metrics"""
        try:
            sdk_service = SDKManagementService(db)
            analytics_data = await sdk_service.get_sdk_analytics(period, language)
            
            return V1ResponseModel(
                success=True,
                data=analytics_data,
                message="SDK usage analytics retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve SDK analytics: {e}")
            raise HTTPException(status_code=502, detail="Failed to retrieve analytics")
    
    @router.post("/feedback", response_model=V1ResponseModel)
    async def submit_sdk_feedback(
        request: Request,
        language: str,
        feedback_type: str,
        rating: int,
        comments: Optional[str] = None,
        context: HTTPRoutingContext = Depends(lambda: permission_guard.require_role(PlatformRole.SI_SERVICE)),
        db = Depends(get_async_session),
    ):
        """Submit feedback for SDK experience"""
        try:
            if not 1 <= rating <= 5:
                raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
            
            sdk_service = SDKManagementService(db)
            
            user_id = getattr(context, 'user_id', 'anonymous')
            organization_id = getattr(context, 'organization_id', 'default')
            
            feedback_data = {
                "feedback_type": feedback_type,
                "rating": rating,
                "comments": comments,
                "is_public": True
            }
            
            result = await sdk_service.submit_sdk_feedback(
                language, user_id, organization_id, feedback_data
            )
            
            return V1ResponseModel(
                success=True,
                data=result,
                message="Feedback submitted successfully"
            )
            
        except ValueError as ve:
            raise HTTPException(status_code=404, detail=str(ve))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            raise HTTPException(status_code=502, detail="Failed to submit feedback")
    
    return router
