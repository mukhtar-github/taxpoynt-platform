"""
SDK Data Seeder
===============
Populates database with initial SDK data, scenarios, and documentation.
Provides both production and development data seeding capabilities.
"""

import logging
import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..data_management.models import (
    SDK, SDKVersion, SandboxScenario, SDKDocumentation, SDKAnalytics,
    SDKLanguage, SDKStatus, DEMO_SDK_DATA, DEMO_SCENARIOS
)
from ..data_management.database_init import get_database_session

logger = logging.getLogger(__name__)

class SDKDataSeeder:
    """
    Service for seeding SDK-related data into the database.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"
        
    async def seed_all_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Seed all SDK-related data."""
        try:
            results = {
                "sdks_created": 0,
                "scenarios_created": 0,
                "documentation_created": 0,
                "analytics_created": 0,
                "errors": []
            }
            
            # Seed SDKs
            sdk_results = await self.seed_sdks(force_refresh)
            results["sdks_created"] = sdk_results["created"]
            if sdk_results.get("errors"):
                results["errors"].extend(sdk_results["errors"])
            
            # Seed scenarios
            scenario_results = await self.seed_sandbox_scenarios(force_refresh)
            results["scenarios_created"] = scenario_results["created"]
            if scenario_results.get("errors"):
                results["errors"].extend(scenario_results["errors"])
            
            # Seed documentation
            doc_results = await self.seed_documentation(force_refresh)
            results["documentation_created"] = doc_results["created"]
            if doc_results.get("errors"):
                results["errors"].extend(doc_results["errors"])
            
            # Seed analytics
            analytics_results = await self.seed_analytics_data(force_refresh)
            results["analytics_created"] = analytics_results["created"]
            if analytics_results.get("errors"):
                results["errors"].extend(analytics_results["errors"])
            
            logger.info(f"Data seeding completed: {results}")
            return results
            
        except Exception as e:
            logger.error(f"Data seeding failed: {e}")
            raise
    
    async def seed_sdks(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Seed SDK catalog data."""
        try:
            created_count = 0
            errors = []
            
            for lang_key, sdk_data in DEMO_SDK_DATA.items():
                try:
                    # Check if SDK already exists
                    existing_sdk = self.db.query(SDK).filter(
                        SDK.language == SDKLanguage(lang_key)
                    ).first()
                    
                    if existing_sdk and not force_refresh:
                        logger.info(f"SDK for {lang_key} already exists, skipping")
                        continue
                    
                    if existing_sdk and force_refresh:
                        # Update existing SDK
                        existing_sdk.name = sdk_data["name"]
                        existing_sdk.version = sdk_data["version"]
                        existing_sdk.description = sdk_data["description"]
                        existing_sdk.features = sdk_data["features"]
                        existing_sdk.requirements = sdk_data["requirements"]
                        existing_sdk.compatibility = sdk_data["compatibility"]
                        existing_sdk.examples = sdk_data["examples"]
                        existing_sdk.download_count = sdk_data["download_count"]
                        existing_sdk.rating = sdk_data["rating"]
                        existing_sdk.status = SDKStatus(sdk_data["status"])
                        existing_sdk.updated_at = datetime.utcnow()
                        logger.info(f"Updated SDK for {lang_key}")
                    else:
                        # Create new SDK
                        new_sdk = SDK(
                            name=sdk_data["name"],
                            language=SDKLanguage(lang_key),
                            version=sdk_data["version"],
                            description=sdk_data["description"],
                            features=sdk_data["features"],
                            requirements=sdk_data["requirements"],
                            compatibility=sdk_data["compatibility"],
                            examples=sdk_data["examples"],
                            download_count=sdk_data["download_count"],
                            rating=sdk_data["rating"],
                            status=SDKStatus(sdk_data["status"]),
                            is_active=True
                        )
                        self.db.add(new_sdk)
                        created_count += 1
                        logger.info(f"Created SDK for {lang_key}")
                    
                except Exception as e:
                    error_msg = f"Failed to seed SDK for {lang_key}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            self.db.commit()
            return {"created": created_count, "errors": errors}
            
        except Exception as e:
            logger.error(f"SDK seeding failed: {e}")
            self.db.rollback()
            raise
    
    async def seed_sandbox_scenarios(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Seed sandbox test scenarios."""
        try:
            created_count = 0
            errors = []
            
            for scenario_key, scenario_data in DEMO_SCENARIOS.items():
                try:
                    # Check if scenario already exists
                    existing_scenario = self.db.query(SandboxScenario).filter(
                        SandboxScenario.name == scenario_data["name"]
                    ).first()
                    
                    if existing_scenario and not force_refresh:
                        logger.info(f"Scenario '{scenario_data['name']}' already exists, skipping")
                        continue
                    
                    if existing_scenario and force_refresh:
                        # Update existing scenario
                        existing_scenario.description = scenario_data["description"]
                        existing_scenario.endpoint = scenario_data["endpoint"]
                        existing_scenario.method = scenario_data["method"]
                        existing_scenario.headers = scenario_data["headers"]
                        existing_scenario.body = scenario_data["body"]
                        existing_scenario.expected_response = scenario_data["expected_response"]
                        existing_scenario.updated_at = datetime.utcnow()
                        logger.info(f"Updated scenario '{scenario_data['name']}'")
                    else:
                        # Create new scenario
                        new_scenario = SandboxScenario(
                            name=scenario_data["name"],
                            description=scenario_data["description"],
                            endpoint=scenario_data["endpoint"],
                            method=scenario_data["method"],
                            headers=scenario_data["headers"],
                            body=scenario_data["body"],
                            expected_response=scenario_data["expected_response"],
                            is_active=True,
                            category="integration_test",
                            difficulty="beginner"
                        )
                        self.db.add(new_scenario)
                        created_count += 1
                        logger.info(f"Created scenario '{scenario_data['name']}'")
                    
                except Exception as e:
                    error_msg = f"Failed to seed scenario '{scenario_key}': {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            self.db.commit()
            return {"created": created_count, "errors": errors}
            
        except Exception as e:
            logger.error(f"Scenario seeding failed: {e}")
            self.db.rollback()
            raise
    
    async def seed_documentation(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Seed SDK documentation."""
        try:
            created_count = 0
            errors = []
            
            # Get all SDKs from database
            sdks = self.db.query(SDK).filter(SDK.is_active == True).all()
            
            for sdk in sdks:
                try:
                    # Documentation types to create
                    doc_types = [
                        ("overview", self._generate_overview_doc(sdk)),
                        ("quick_start", self._generate_quickstart_doc(sdk)),
                        ("api_reference", self._generate_api_reference_doc(sdk)),
                        ("examples", self._generate_examples_doc(sdk)),
                        ("troubleshooting", self._generate_troubleshooting_doc(sdk))
                    ]
                    
                    for doc_type, content in doc_types:
                        # Check if documentation already exists
                        existing_doc = self.db.query(SDKDocumentation).filter(
                            SDKDocumentation.sdk_id == sdk.id,
                            SDKDocumentation.content_type == doc_type,
                            SDKDocumentation.language == "en"
                        ).first()
                        
                        if existing_doc and not force_refresh:
                            continue
                        
                        if existing_doc and force_refresh:
                            # Update existing documentation
                            existing_doc.content = content
                            existing_doc.version = sdk.version
                            existing_doc.updated_at = datetime.utcnow()
                        else:
                            # Create new documentation
                            new_doc = SDKDocumentation(
                                sdk_id=sdk.id,
                                language="en",
                                content_type=doc_type,
                                content=content,
                                version=sdk.version,
                                is_published=True
                            )
                            self.db.add(new_doc)
                            created_count += 1
                    
                    logger.info(f"Seeded documentation for {sdk.name}")
                    
                except Exception as e:
                    error_msg = f"Failed to seed documentation for {sdk.name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            self.db.commit()
            return {"created": created_count, "errors": errors}
            
        except Exception as e:
            logger.error(f"Documentation seeding failed: {e}")
            self.db.rollback()
            raise
    
    async def seed_analytics_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Seed historical analytics data."""
        try:
            created_count = 0
            errors = []
            
            # Get all SDKs from database
            sdks = self.db.query(SDK).filter(SDK.is_active == True).all()
            
            # Generate analytics for the last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            
            for sdk in sdks:
                try:
                    # Generate daily analytics for the past 30 days
                    current_date = start_date
                    while current_date <= end_date:
                        # Check if analytics already exist for this date
                        existing_analytics = self.db.query(SDKAnalytics).filter(
                            SDKAnalytics.sdk_id == sdk.id,
                            SDKAnalytics.date == current_date.date(),
                            SDKAnalytics.period == "daily"
                        ).first()
                        
                        if existing_analytics and not force_refresh:
                            current_date += timedelta(days=1)
                            continue
                        
                        # Generate realistic analytics data
                        analytics_data = self._generate_analytics_for_date(sdk, current_date)
                        
                        if existing_analytics and force_refresh:
                            # Update existing analytics
                            for key, value in analytics_data.items():
                                if hasattr(existing_analytics, key):
                                    setattr(existing_analytics, key, value)
                            existing_analytics.updated_at = datetime.utcnow()
                        else:
                            # Create new analytics
                            new_analytics = SDKAnalytics(
                                sdk_id=sdk.id,
                                date=current_date,
                                period="daily",
                                **analytics_data
                            )
                            self.db.add(new_analytics)
                            created_count += 1
                        
                        current_date += timedelta(days=1)
                    
                    logger.info(f"Seeded analytics for {sdk.name}")
                    
                except Exception as e:
                    error_msg = f"Failed to seed analytics for {sdk.name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
            
            self.db.commit()
            return {"created": created_count, "errors": errors}
            
        except Exception as e:
            logger.error(f"Analytics seeding failed: {e}")
            self.db.rollback()
            raise
    
    def _generate_overview_doc(self, sdk: SDK) -> Dict[str, Any]:
        """Generate overview documentation."""
        return {
            "title": f"{sdk.name} Overview",
            "description": sdk.description,
            "version": sdk.version,
            "status": sdk.status.value,
            "features": sdk.features,
            "compatibility": sdk.compatibility,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _generate_quickstart_doc(self, sdk: SDK) -> Dict[str, Any]:
        """Generate quick start documentation."""
        lang = sdk.language.value
        return {
            "title": "Quick Start Guide",
            "steps": [
                f"Install the {sdk.name}",
                "Configure your API credentials",
                "Create your first invoice",
                "Handle webhook notifications"
            ],
            "installation": f"pip install taxpoynt-{lang}" if lang == "python" else f"npm install @taxpoynt/{lang}-sdk",
            "basic_example": f"# Example code for {sdk.name}\n# Implementation details here",
            "next_steps": [
                "Explore advanced features",
                "Read API reference",
                "Check out examples"
            ]
        }
    
    def _generate_api_reference_doc(self, sdk: SDK) -> Dict[str, Any]:
        """Generate API reference documentation."""
        return {
            "title": "API Reference",
            "classes": [
                {
                    "name": "TaxPoyntClient",
                    "description": "Main client class for TaxPoynt integration",
                    "methods": [
                        {
                            "name": "create_invoice",
                            "description": "Create a new invoice",
                            "parameters": ["invoice_data"],
                            "returns": "Invoice object"
                        },
                        {
                            "name": "get_invoice",
                            "description": "Retrieve an existing invoice",
                            "parameters": ["invoice_id"],
                            "returns": "Invoice object"
                        }
                    ]
                }
            ],
            "examples": sdk.examples
        }
    
    def _generate_examples_doc(self, sdk: SDK) -> Dict[str, Any]:
        """Generate examples documentation."""
        return {
            "title": "Code Examples",
            "examples": [
                {
                    "name": example,
                    "description": f"Example showing how to {example.lower()}",
                    "code": f"# {example} example code here\n# Implementation details...",
                    "language": sdk.language.value
                }
                for example in sdk.examples
            ]
        }
    
    def _generate_troubleshooting_doc(self, sdk: SDK) -> Dict[str, Any]:
        """Generate troubleshooting documentation."""
        return {
            "title": "Troubleshooting Guide",
            "common_issues": [
                {
                    "issue": "Authentication Errors",
                    "solution": "Verify your API key and secret are correct",
                    "code_example": "client.test_connection()"
                },
                {
                    "issue": "Rate Limiting",
                    "solution": "Implement exponential backoff retry logic",
                    "code_example": "# Retry logic example"
                },
                {
                    "issue": "Webhook Delivery Issues",
                    "solution": "Check webhook endpoint configuration and SSL certificate",
                    "code_example": "# Webhook handler example"
                }
            ],
            "support_contact": "sdk-support@taxpoynt.com"
        }
    
    def _generate_analytics_for_date(self, sdk: SDK, date: datetime) -> Dict[str, Any]:
        """Generate realistic analytics data for a specific date."""
        import random
        
        # Base values influenced by SDK popularity
        base_downloads = max(1, sdk.download_count // 30)  # Average daily downloads
        base_users = max(1, int(base_downloads * 0.7))     # 70% of downloads are active users
        base_api_calls = max(10, base_users * 25)          # 25 API calls per user on average
        
        # Add some randomness to make it realistic
        downloads = max(0, int(base_downloads + random.randint(-5, 10)))
        active_users = max(0, int(base_users + random.randint(-3, 7)))
        api_calls = max(0, int(base_api_calls + random.randint(-50, 100)))
        
        # Response time varies by language (compiled languages are faster)
        response_times = {
            "go": (50, 150),
            "java": (80, 200),
            "csharp": (70, 180),
            "rust": (40, 120),
            "python": (100, 300),
            "javascript": (90, 250),
            "ruby": (120, 350),
            "php": (110, 320),
            "swift": (60, 160),
            "kotlin": (85, 210)
        }
        
        min_time, max_time = response_times.get(sdk.language.value, (100, 300))
        avg_response_time = random.randint(min_time, max_time)
        
        # Error rate is generally low but varies by maturity
        error_rates = {
            "stable": (0.01, 0.05),
            "beta": (0.02, 0.08),
            "draft": (0.05, 0.15),
            "deprecated": (0.08, 0.20)
        }
        
        min_error, max_error = error_rates.get(sdk.status.value, (0.02, 0.08))
        error_rate = round(random.uniform(min_error, max_error), 4)
        
        return {
            "downloads": downloads,
            "active_users": active_users,
            "api_calls": api_calls,
            "avg_response_time": avg_response_time,
            "error_rate": error_rate,
            "top_features": sdk.features[:3],  # Top 3 features
            "top_organizations": ["TechCorp", "FinanceHub", "RetailPlus"]
        }


async def seed_sdk_data(force_refresh: bool = False) -> Dict[str, Any]:
    """Convenience function to seed SDK data."""
    db_session = get_database_session()
    seeder = SDKDataSeeder(db_session)
    try:
        return await seeder.seed_all_data(force_refresh)
    finally:
        db_session.close()


if __name__ == "__main__":
    # Run seeding if called directly
    async def main():
        print("Starting SDK data seeding...")
        results = await seed_sdk_data(force_refresh=True)
        print(f"Seeding completed: {results}")
    
    asyncio.run(main())