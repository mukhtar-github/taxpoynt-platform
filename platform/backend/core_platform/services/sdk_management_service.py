"""
SDK Management Service
======================
Service layer for SDK management operations with database integration
and demo data fallbacks for development/testing environments.
"""

import logging
import os
import zipfile
import tempfile
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func, desc, select

from ..data_management.models import (
    SDK, SDKVersion, SDKDownload, SDKUsageLog, SandboxScenario, 
    SandboxTestResult, SDKDocumentation, SDKFeedback, SDKAnalytics,
    SDKLanguage, SDKStatus, FeedbackType, TestStatus,
    DEMO_SDK_DATA, DEMO_SCENARIOS
)
from ..data_management.models.user import User
from ..data_management.models.organization import Organization

logger = logging.getLogger(__name__)

class SDKManagementService:
    """
    Service for managing SDK operations including database operations
    and demo data fallbacks.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.use_demo_data = os.getenv("USE_DEMO_DATA", "false").lower() == "true"
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
        logger.info(f"SDK Management Service initialized - Demo Mode: {self.demo_mode}, Use Demo Data: {self.use_demo_data}")
    
    # ==================== SDK Catalog Operations ====================
    
    async def get_sdk_catalog(self, language: Optional[str] = None) -> Dict[str, Any]:
        """Get SDK catalog with optional language filtering."""
        try:
            if self.use_demo_data or self.demo_mode:
                return await self._get_demo_sdk_catalog(language)
            
            return await self._get_database_sdk_catalog(language)
            
        except Exception as e:
            logger.error(f"Failed to get SDK catalog: {e}")
            # Fallback to demo data on error
            return await self._get_demo_sdk_catalog(language)
    
    async def _get_demo_sdk_catalog(self, language: Optional[str] = None) -> Dict[str, Any]:
        """Get demo SDK catalog data."""
        catalog = DEMO_SDK_DATA.copy()
        
        if language:
            catalog = {k: v for k, v in catalog.items() if v["language"] == language}
        
        return {
            "sdk_catalog": catalog,
            "total_count": len(catalog),
            "languages_available": list(set(sdk["language"] for sdk in catalog.values())),
            "source": "demo_data"
        }
    
    async def _get_database_sdk_catalog(self, language: Optional[str] = None) -> Dict[str, Any]:
        """Get SDK catalog from database (async)."""
        stmt = select(SDK).where(SDK.is_active == True)
        if language:
            stmt = stmt.where(SDK.language == language)
        res = await self.db.execute(stmt)
        sdks = res.scalars().all()
        
        catalog = {}
        for sdk in sdks:
            catalog[sdk.language.value] = {
                "id": str(sdk.id),
                "name": sdk.name,
                "language": sdk.language.value,
                "version": sdk.version,
                "description": sdk.description,
                "features": sdk.features,
                "requirements": sdk.requirements,
                "compatibility": sdk.compatibility,
                "examples": sdk.examples,
                "download_count": sdk.download_count,
                "rating": float(sdk.rating) if sdk.rating else 0.0,
                "status": sdk.status.value,
                "last_updated": sdk.updated_at.isoformat() if sdk.updated_at else sdk.created_at.isoformat()
            }
        
        return {
            "sdk_catalog": catalog,
            "total_count": len(catalog),
            "languages_available": list(set(sdk["language"] for sdk in catalog.values())),
            "source": "database"
        }
    
    async def get_sdk_by_language(self, language: str) -> Optional[Dict[str, Any]]:
        """Get specific SDK by programming language."""
        try:
            if self.use_demo_data or self.demo_mode:
                return DEMO_SDK_DATA.get(language)
            
            res = await self.db.execute(
                select(SDK).where(and_(SDK.language == language, SDK.is_active == True)).limit(1)
            )
            sdk = res.scalars().first()
            
            if not sdk:
                return None
            
            return {
                "id": str(sdk.id),
                "name": sdk.name,
                "language": sdk.language.value,
                "version": sdk.version,
                "description": sdk.description,
                "features": sdk.features,
                "requirements": sdk.requirements,
                "compatibility": sdk.compatibility,
                "examples": sdk.examples,
                "download_count": sdk.download_count,
                "rating": float(sdk.rating) if sdk.rating else 0.0,
                "status": sdk.status.value,
                "last_updated": sdk.updated_at.isoformat() if sdk.updated_at else sdk.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get SDK for {language}: {e}")
            # Fallback to demo data
            return DEMO_SDK_DATA.get(language)
    
    # ==================== Sandbox Operations ====================
    
    async def get_sandbox_scenarios(self) -> Dict[str, Any]:
        """Get available sandbox test scenarios."""
        try:
            if self.use_demo_data or self.demo_mode:
                return {"scenarios": DEMO_SCENARIOS, "source": "demo_data"}
            
            res = await self.db.execute(select(SandboxScenario).where(SandboxScenario.is_active == True))
            scenarios = res.scalars().all()
            
            scenario_dict = {}
            for scenario in scenarios:
                scenario_dict[scenario.name.lower().replace(" ", "_")] = {
                    "id": str(scenario.id),
                    "name": scenario.name,
                    "description": scenario.description,
                    "endpoint": scenario.endpoint,
                    "method": scenario.method,
                    "headers": scenario.headers,
                    "body": scenario.body,
                    "expected_response": scenario.expected_response
                }
            
            return {"scenarios": scenario_dict, "source": "database"}
            
        except Exception as e:
            logger.error(f"Failed to get sandbox scenarios: {e}")
            return {"scenarios": DEMO_SCENARIOS, "source": "demo_data_fallback"}
    
    async def execute_sandbox_test(self, scenario_name: str, user_id: str, organization_id: str,
                                  test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a sandbox test and record results."""
        try:
            # Get scenario
            scenarios_data = await self.get_sandbox_scenarios()
            scenario = scenarios_data["scenarios"].get(scenario_name)
            
            if not scenario:
                raise ValueError(f"Scenario '{scenario_name}' not found")
            
            # Execute test (simulate API call)
            test_result = await self._simulate_api_test(scenario, test_data)
            
            # Record test result in database
            if not self.use_demo_data and not self.demo_mode:
                await self._record_test_result(scenario_name, user_id, organization_id, test_result, test_data)
            
            return test_result
            
        except Exception as e:
            logger.error(f"Sandbox test execution failed: {e}")
            raise
    
    async def _simulate_api_test(self, scenario: Dict[str, Any], test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate API test execution."""
        import asyncio
        await asyncio.sleep(0.5)  # Simulate network delay
        
        # Mock successful response
        return {
            "scenario": scenario["name"],
            "status": "success",
            "response_time_ms": 450,
            "status_code": 200,
            "response_body": scenario.get("expected_response", {"status": "success"}),
            "headers_sent": {**scenario.get("headers", {}), **test_data.get("custom_headers", {})},
            "body_sent": test_data.get("custom_body") or scenario.get("body"),
            "tested_at": datetime.utcnow().isoformat()
        }
    
    async def _record_test_result(self, scenario_name: str, user_id: str, organization_id: str,
                                 test_result: Dict[str, Any], test_data: Dict[str, Any]) -> None:
        """Record test result in database."""
        try:
            # Find scenario in database
            res = await self.db.execute(select(SandboxScenario).where(SandboxScenario.name == scenario_name).limit(1))
            scenario = res.scalars().first()
            
            if not scenario:
                return
            
            # Create test result record
            result = SandboxTestResult(
                scenario_id=scenario.id,
                user_id=user_id,
                organization_id=organization_id,
                status=TestStatus.SUCCESS if test_result["status"] == "success" else TestStatus.FAILED,
                response_time=test_result["response_time_ms"],
                status_code=test_result["status_code"],
                response_body=test_result["response_body"],
                headers_sent=test_result["headers_sent"],
                body_sent=test_result["body_sent"],
                metadata=test_data
            )
            
            self.db.add(result)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record test result: {e}")
            await self.db.rollback()
    
    # ==================== Helper Methods ====================
    
    def _generate_readme(self, sdk_name: str, sdk_info: Dict[str, Any]) -> str:
        """Generate README content for SDK."""
        return f"""# TaxPoynt {sdk_name.upper()} SDK

Generated on: {datetime.utcnow().isoformat()}

## Description
{sdk_info.get('description', 'Official SDK for TaxPoynt platform integration')}

## Features
{chr(10).join(f"- {feature}" for feature in sdk_info.get('features', []))}

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

## Requirements
{chr(10).join(f"- {req}" for req in sdk_info.get('requirements', []))}

## Documentation
Visit: https://docs.taxpoynt.com/sdk/{sdk_name.lower()}
"""
    
    def _generate_sdk_code(self, sdk_name: str, sdk_info: Dict[str, Any]) -> str:
        """Generate main SDK code file."""
        return f"""# TaxPoynt {sdk_name.upper()} SDK
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
    
    def get_business_systems(self):
        response = self.session.get(f"{{self.base_url}}/api/v1/si/business-systems")
        return response.json()
"""
    
    def _generate_requirements(self, sdk_info: Dict[str, Any]) -> str:
        """Generate requirements.txt content."""
        requirements = sdk_info.get('requirements', [])
        if not requirements:
            requirements = ["requests>=2.25.0", "pydantic>=1.8.0", "python-dotenv>=0.19.0"]
        
        return "\n".join(requirements)
    
    # ==================== SDK Generation Operations ====================
    
    async def generate_sdk_package(self, language: str, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate SDK package files for download."""
        try:
            sdk_info = await self.get_sdk_by_language(language)
            if not sdk_info:
                raise ValueError(f"SDK for language '{language}' not found")
            
            # Create temporary directory for SDK files
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create SDK structure
                sdk_dir = temp_path / f"{language}_sdk"
                sdk_dir.mkdir()
                
                # Generate files
                readme_content = self._generate_readme(language, sdk_info)
                sdk_code = self._generate_sdk_code(language, sdk_info)
                requirements = self._generate_requirements(sdk_info)
                
                # Write files
                (sdk_dir / "README.md").write_text(readme_content)
                (sdk_dir / f"taxpoynt_{language.lower()}.py").write_text(sdk_code)
                (sdk_dir / "requirements.txt").write_text(requirements)
                
                # Create examples directory
                examples_dir = sdk_dir / "examples"
                examples_dir.mkdir()
                
                # Generate example files
                for example in sdk_info.get('examples', []):
                    example_file = examples_dir / f"{example.lower().replace(' ', '_')}.py"
                    example_content = self._generate_example_code(language, example, sdk_info)
                    example_file.write_text(example_content)
                
                # Create ZIP file
                import zipfile
                zip_path = temp_path / f"{language}_sdk.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in sdk_dir.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(sdk_dir)
                            zipf.write(file_path, arcname)
                
                # Calculate file size and checksum
                file_size = zip_path.stat().st_size
                checksum = self._calculate_file_checksum(zip_path)
                
                return {
                    "sdk_path": str(zip_path),
                    "language": language,
                    "file_size": file_size,
                    "checksum": checksum,
                    "generated_at": datetime.utcnow().isoformat(),
                    "download_url": f"/api/v1/si/sdk/download/{language}_sdk.zip"
                }
                
        except Exception as e:
            logger.error(f"SDK generation failed for {language}: {e}")
            raise
    
    def _generate_example_code(self, language: str, example: str, sdk_info: Dict[str, Any]) -> str:
        """Generate example code for specific use cases."""
        example_templates = {
            "Basic Integration": f'''# {example} Example for TaxPoynt {language.upper()} SDK

from taxpoynt import TaxPoyntClient
import os

# Initialize client
client = TaxPoyntClient(
    api_key=os.getenv("TAXPOYNT_API_KEY"),
    base_url=os.getenv("TAXPOYNT_BASE_URL", "https://api.taxpoynt.com")
)

# Basic usage
try:
    # Test connection
    response = client.get_business_systems()
    print("Connected successfully:", response)
    
    # Basic invoice creation
    invoice_data = {{
        "invoice_number": "INV-001",
        "amount": 1000.00,
        "currency": "NGN",
        "customer_name": "Test Customer",
        "items": [
            {{
                "name": "Test Item",
                "quantity": 1,
                "unit_price": 1000.00
            }}
        ]
    }}
    
    invoice = client.create_invoice(invoice_data)
    print("Invoice created:", invoice)
    
except Exception as e:
    print(f"Error: {{e}}")
''',
            "Invoice Creation": f'''# {example} Example for TaxPoynt {language.upper()} SDK

from taxpoynt import TaxPoyntClient
from datetime import datetime
import os

# Initialize client
client = TaxPoyntClient(
    api_key=os.getenv("TAXPOYNT_API_KEY"),
    base_url=os.getenv("TAXPOYNT_BASE_URL", "https://api.taxpoynt.com")
)

def create_sample_invoice():
    """Create a sample invoice with detailed information."""
    
    invoice_data = {{
        "invoice_number": f"INV-{{datetime.now().strftime('%Y%m%d-%H%M%S')}}",
        "issue_date": datetime.now().isoformat(),
        "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "customer": {{
            "name": "Sample Customer Ltd",
            "email": "customer@example.com",
            "address": "123 Business Street, Lagos, Nigeria",
            "tax_id": "12345678-0001"
        }},
        "items": [
            {{
                "description": "Professional Services",
                "quantity": 1,
                "unit_price": 50000.00,
                "vat_rate": 0.075,
                "total": 53750.00
            }},
            {{
                "description": "Consulting Hours",
                "quantity": 10,
                "unit_price": 5000.00,
                "vat_rate": 0.075,
                "total": 53750.00
            }}
        ],
        "subtotal": 100000.00,
        "vat_total": 7500.00,
        "total_amount": 107500.00,
        "currency": "NGN"
    }}
    
    try:
        response = client.create_invoice(invoice_data)
        print("Invoice created successfully:")
        print(f"Invoice ID: {{response.get('invoice_id')}}")
        print(f"Status: {{response.get('status')}}")
        return response
        
    except Exception as e:
        print(f"Invoice creation failed: {{e}}")
        return None

if __name__ == "__main__":
    create_sample_invoice()
''',
            "Webhook Processing": f'''# {example} Example for TaxPoynt {language.upper()} SDK

from taxpoynt import TaxPoyntClient
from flask import Flask, request, jsonify
import os
import hashlib
import hmac

app = Flask(__name__)

# Initialize client
client = TaxPoyntClient(
    api_key=os.getenv("TAXPOYNT_API_KEY"),
    base_url=os.getenv("TAXPOYNT_BASE_URL", "https://api.taxpoynt.com")
)

WEBHOOK_SECRET = os.getenv("TAXPOYNT_WEBHOOK_SECRET")

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature for security."""
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={{expected_signature}}", signature)

@app.route('/webhooks/taxpoynt', methods=['POST'])
def handle_webhook():
    """Handle incoming TaxPoynt webhooks."""
    
    # Verify signature
    signature = request.headers.get('X-TaxPoynt-Signature')
    if not signature or not verify_webhook_signature(request.data, signature, WEBHOOK_SECRET):
        return jsonify({{"error": "Invalid signature"}}), 401
    
    # Process webhook data
    webhook_data = request.json
    event_type = webhook_data.get('event_type')
    
    try:
        if event_type == 'invoice.created':
            handle_invoice_created(webhook_data)
        elif event_type == 'invoice.updated':
            handle_invoice_updated(webhook_data)
        elif event_type == 'payment.completed':
            handle_payment_completed(webhook_data)
        else:
            print(f"Unknown event type: {{event_type}}")
        
        return jsonify({{"status": "success"}}), 200
        
    except Exception as e:
        print(f"Webhook processing failed: {{e}}")
        return jsonify({{"error": "Processing failed"}}), 500

def handle_invoice_created(data):
    """Handle invoice creation webhook."""
    invoice_id = data.get('data', {{}}).get('invoice_id')
    print(f"Invoice created: {{invoice_id}}")
    
    # Fetch full invoice details
    invoice = client.get_invoice(invoice_id)
    print(f"Invoice details: {{invoice}}")

def handle_invoice_updated(data):
    """Handle invoice update webhook."""
    invoice_id = data.get('data', {{}}).get('invoice_id')
    print(f"Invoice updated: {{invoice_id}}")

def handle_payment_completed(data):
    """Handle payment completion webhook."""
    payment_id = data.get('data', {{}}).get('payment_id')
    print(f"Payment completed: {{payment_id}}")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
'''
        }
        
        return example_templates.get(example, f"# {example} example code here")
    
    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    # ==================== Analytics Operations ====================
    
    async def get_sdk_analytics(self, period: str = "30d", language: Optional[str] = None) -> Dict[str, Any]:
        """Get SDK usage analytics and metrics."""
        try:
            if self.use_demo_data or self.demo_mode:
                return await self._get_demo_analytics(period, language)
            
            return await self._get_database_analytics(period, language)
            
        except Exception as e:
            logger.error(f"Failed to get SDK analytics: {e}")
            return await self._get_demo_analytics(period, language)
    
    async def _get_demo_analytics(self, period: str, language: Optional[str]) -> Dict[str, Any]:
        """Get demo analytics data."""
        catalog = DEMO_SDK_DATA
        
        if language:
            catalog = {k: v for k, v in catalog.items() if k == language}
        
        analytics = {
            "period": period,
            "total_downloads": sum(sdk["download_count"] for sdk in catalog.values()),
            "downloads_by_language": {lang: sdk["download_count"] for lang, sdk in catalog.items()},
            "popular_features": ["Authentication", "Invoice Management", "Compliance Checking"],
            "integration_success_rate": 0.94,
            "average_response_time_ms": 245,
            "error_rate": 0.06,
            "top_organizations": ["TechCorp", "FinanceHub", "RetailPlus"],
            "generated_at": datetime.utcnow().isoformat(),
            "source": "demo_data"
        }
        
        return {"analytics": analytics}
    
    async def _get_database_analytics(self, period: str, language: Optional[str]) -> Dict[str, Any]:
        """Get analytics from database."""
        # Calculate date range based on period
        if period == "30d":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "7d":
            start_date = datetime.utcnow() - timedelta(days=7)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        # Query analytics from database
        stmt = select(SDKAnalytics).where(SDKAnalytics.date >= start_date)
        if language:
            res_sdk = await self.db.execute(select(SDK).where(SDK.language == language).limit(1))
            sdk_row = res_sdk.scalars().first()
            if sdk_row:
                stmt = stmt.where(SDKAnalytics.sdk_id == sdk_row.id)
        res = await self.db.execute(stmt)
        analytics_data = res.scalars().all()
        
        # Aggregate results
        total_downloads = sum(a.downloads for a in analytics_data if a.downloads)
        total_api_calls = sum(a.api_calls for a in analytics_data if a.api_calls)
        avg_response_time = sum(a.avg_response_time for a in analytics_data if a.avg_response_time) / len(analytics_data) if analytics_data else 0
        avg_error_rate = sum(float(a.error_rate) for a in analytics_data if a.error_rate) / len(analytics_data) if analytics_data else 0
        
        return {
            "analytics": {
                "period": period,
                "total_downloads": total_downloads,
                "total_api_calls": total_api_calls,
                "average_response_time_ms": int(avg_response_time),
                "error_rate": round(avg_error_rate, 4),
                "generated_at": datetime.utcnow().isoformat(),
                "source": "database"
            }
        }
    
    # ==================== Feedback Operations ====================
    
    async def submit_sdk_feedback(self, language: str, user_id: str, organization_id: str,
                                 feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit feedback for SDK experience."""
        try:
            if self.use_demo_data or self.demo_mode:
                # Just log and return success for demo mode
                logger.info(f"Demo feedback submitted for {language}: {feedback_data}")
                return {
                    "feedback_id": f"demo-{language}-{datetime.utcnow().timestamp()}",
                    "status": "submitted",
                    "source": "demo_data"
                }
            
            # Get SDK
            res = await self.db.execute(
                select(SDK).where(and_(SDK.language == language, SDK.is_active == True)).limit(1)
            )
            sdk = res.scalars().first()
            
            if not sdk:
                raise ValueError(f"SDK for language '{language}' not found")
            
            # Create feedback record
            feedback = SDKFeedback(
                sdk_id=sdk.id,
                user_id=user_id,
                organization_id=organization_id,
                feedback_type=FeedbackType(feedback_data.get('feedback_type', 'general')),
                rating=feedback_data['rating'],
                comments=feedback_data.get('comments'),
                is_public=feedback_data.get('is_public', True)
            )
            
            self.db.add(feedback)
            await self.db.commit()
            
            return {
                "feedback_id": str(feedback.id),
                "status": "submitted",
                "source": "database"
            }
            
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            if not self.use_demo_data:
                await self.db.rollback()
            raise
