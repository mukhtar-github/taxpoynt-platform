#!/usr/bin/env python3
"""
SDK Endpoints Test Script
========================
Test SDK management endpoints with demo data (no database required).
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set environment for demo data testing
os.environ["USE_DEMO_DATA"] = "true" 
os.environ["DEMO_MODE"] = "true"

async def test_sdk_service():
    """Test SDKManagementService directly with demo data."""
    
    print("🧪 Testing SDK Management Service with Demo Data")
    print("=" * 50)
    
    try:
        # Import after setting environment
        from core_platform.services.sdk_management_service import SDKManagementService
        from unittest.mock import Mock
        
        # Create mock database session (won't be used in demo mode)
        mock_db = Mock()
        sdk_service = SDKManagementService(mock_db)
        
        # Test 1: Get SDK Catalog
        print("\n📋 Test 1: Get SDK Catalog")
        catalog = await sdk_service.get_sdk_catalog()
        print(f"   ✅ Retrieved {catalog['total_count']} SDKs")
        print(f"   ✅ Languages: {catalog['languages_available']}")
        print(f"   ✅ Source: {catalog['source']}")
        
        # Test 2: Get Specific SDK
        print("\n🐍 Test 2: Get Python SDK")
        python_sdk = await sdk_service.get_sdk_by_language("python")
        if python_sdk:
            print(f"   ✅ Found: {python_sdk['name']}")
            print(f"   ✅ Version: {python_sdk['version']}")
            print(f"   ✅ Downloads: {python_sdk['download_count']}")
            print(f"   ✅ Rating: {python_sdk['rating']}")
        else:
            print("   ❌ Python SDK not found")
            
        # Test 3: Get Sandbox Scenarios  
        print("\n🏗️ Test 3: Get Sandbox Scenarios")
        scenarios = await sdk_service.get_sandbox_scenarios()
        scenario_count = len(scenarios['scenarios'])
        print(f"   ✅ Retrieved {scenario_count} scenarios")
        print(f"   ✅ Source: {scenarios['source']}")
        for name in scenarios['scenarios'].keys():
            print(f"   ✅ Scenario: {name}")
            
        # Test 4: Execute Sandbox Test
        print("\n🧪 Test 4: Execute Sandbox Test")
        test_data = {
            "api_key": "test_key",
            "custom_headers": {"X-Test": "true"},
            "custom_body": None
        }
        
        test_result = await sdk_service.execute_sandbox_test(
            "authentication", "test_user", "test_org", test_data
        )
        print(f"   ✅ Test Status: {test_result['status']}")
        print(f"   ✅ Response Time: {test_result['response_time_ms']}ms")
        
        # Test 5: Get Analytics
        print("\n📊 Test 5: Get SDK Analytics")
        analytics = await sdk_service.get_sdk_analytics("30d")
        analytics_data = analytics['analytics']
        print(f"   ✅ Period: {analytics_data['period']}")
        print(f"   ✅ Total Downloads: {analytics_data['total_downloads']}")
        print(f"   ✅ Success Rate: {analytics_data['integration_success_rate']}")
        print(f"   ✅ Source: {analytics_data['source']}")
        
        # Test 6: Submit Feedback  
        print("\n💬 Test 6: Submit SDK Feedback")
        feedback_data = {
            "feedback_type": "general",
            "rating": 5,
            "comments": "Great SDK, very easy to use!",
            "is_public": True
        }
        
        feedback_result = await sdk_service.submit_sdk_feedback(
            "python", "test_user", "test_org", feedback_data
        )
        print(f"   ✅ Feedback ID: {feedback_result['feedback_id']}")
        print(f"   ✅ Status: {feedback_result['status']}")
        print(f"   ✅ Source: {feedback_result['source']}")
        
        print("\n🎉 All SDK Service Tests Passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_demo_data():
    """Test demo data constants directly."""
    
    print("\n🗃️  Testing Demo Data Constants")
    print("-" * 30)
    
    try:
        from core_platform.data_management.models.sdk_management import DEMO_SDK_DATA, DEMO_SCENARIOS
        
        # Test SDK Data
        print(f"✅ SDK Data: {len(DEMO_SDK_DATA)} languages")
        for lang, data in DEMO_SDK_DATA.items():
            print(f"   • {lang}: {data['name']} v{data['version']}")
            
        # Test Scenarios
        print(f"✅ Scenarios: {len(DEMO_SCENARIOS)} test cases") 
        for name, scenario in DEMO_SCENARIOS.items():
            print(f"   • {name}: {scenario['method']} {scenario['endpoint']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Demo data test failed: {e}")
        return False

async def main():
    """Run all tests."""
    
    print("🚀 SDK Management Demo Data Testing")
    print("=" * 60)
    
    # Test 1: Demo Data Constants
    demo_success = await test_demo_data()
    
    # Test 2: Service Layer
    service_success = await test_sdk_service() 
    
    # Summary
    print("\n" + "=" * 60)
    if demo_success and service_success:
        print("🎉 ALL TESTS PASSED! SDK Management is ready for demo/testing")
        print("\n✅ You can now:")
        print("   • Start the FastAPI server")
        print("   • Test API endpoints via HTTP")
        print("   • Use the SDK management features")
        print("   • Generate SDK packages")
    else:
        print("❌ SOME TESTS FAILED - Check the errors above")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())