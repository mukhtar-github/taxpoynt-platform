#!/usr/bin/env python3
"""
PHASE 2 Integration Test Runner
==============================

Quick validation runner for PHASE 2 integration testing setup.
Validates that the new platform architecture can successfully:

1. Connect to FIRS sandbox using proven credentials
2. Connect to Odoo using existing proven service
3. Perform end-to-end integration testing

This runner provides immediate feedback on PHASE 2 readiness.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the integration tests to Python path
integration_tests_path = Path(__file__).parent / "integration"
sys.path.append(str(integration_tests_path))

try:
    from test_firs_connectivity import FIRSConnectivityTester
    from test_odoo_firs_integration import IntegratedTester
    TESTS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Could not import integration tests: {e}")
    TESTS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'/tmp/phase2_integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)


async def validate_environment():
    """Validate environment configuration for PHASE 2 testing"""
    logger.info("🔍 Validating PHASE 2 Environment Configuration")
    
    # Check critical environment variables
    required_vars = [
        "FIRS_SANDBOX_URL",
        "FIRS_SANDBOX_API_KEY", 
        "FIRS_SANDBOX_API_SECRET",
        "ODOO_HOST",
        "ODOO_DATABASE",
        "ODOO_USERNAME",
        "ODOO_PASSWORD"
    ]
    
    missing_vars = []
    present_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            present_vars.append(var)
            # Log without exposing sensitive values
            if "PASSWORD" in var or "SECRET" in var or "KEY" in var:
                logger.info(f"✅ {var}: {'*' * min(len(value), 8)}")
            else:
                logger.info(f"✅ {var}: {value}")
        else:
            missing_vars.append(var)
            logger.error(f"❌ {var}: NOT SET")
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("❌ Please ensure .env file is properly configured")
        return False
    
    logger.info(f"✅ Environment validation passed: {len(present_vars)}/{len(required_vars)} variables configured")
    return True


async def run_quick_firs_test():
    """Run a quick FIRS connectivity test"""
    logger.info("🚀 Running Quick FIRS Connectivity Test")
    
    if not TESTS_AVAILABLE:
        logger.error("❌ Integration tests not available")
        return False
    
    try:
        tester = FIRSConnectivityTester()
        await tester.setup()
        
        # Run core tests only for quick validation
        core_tests = [
            ("Health Check", tester.test_health_check),
            ("Get Currencies", tester.test_get_currencies),
            ("Get Invoice Types", tester.test_get_invoice_types)
        ]
        
        passed = 0
        for test_name, test_method in core_tests:
            try:
                logger.info(f"⏳ Running {test_name}...")
                result = await test_method()
                if result:
                    logger.info(f"✅ {test_name}: PASS")
                    passed += 1
                else:
                    logger.error(f"❌ {test_name}: FAIL")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"❌ {test_name} failed: {str(e)}")
        
        await tester.teardown()
        
        success = passed >= 2  # Need at least 2/3 to pass
        if success:
            logger.info(f"✅ FIRS Quick Test: PASS ({passed}/3 tests passed)")
        else:
            logger.error(f"❌ FIRS Quick Test: FAIL ({passed}/3 tests passed)")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ FIRS quick test failed: {str(e)}")
        return False


async def run_integrated_test():
    """Run the full integrated test suite"""
    logger.info("🚀 Running Integrated Odoo-FIRS Test")
    
    if not TESTS_AVAILABLE:
        logger.error("❌ Integration tests not available")
        return False
    
    try:
        tester = IntegratedTester()
        results = await tester.run_all_tests()
        
        # Analyze results
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        success = passed >= (total * 0.75)  # 75% success rate required
        
        if success:
            logger.info(f"✅ Integrated Test: PASS ({passed}/{total} components)")
        else:
            logger.error(f"❌ Integrated Test: FAIL ({passed}/{total} components)")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Integrated test failed: {str(e)}")
        return False


async def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("🚀 TAXPOYNT PHASE 2 INTEGRATION TEST RUNNER")
    print("="*80)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = {
        "environment_validation": False,
        "firs_connectivity": False,
        "integrated_test": False
    }
    
    try:
        # Step 1: Validate environment
        logger.info("\n🔧 STEP 1: Environment Validation")
        results["environment_validation"] = await validate_environment()
        
        if not results["environment_validation"]:
            logger.error("❌ Environment validation failed - cannot proceed")
            return results
        
        # Step 2: Quick FIRS test
        logger.info("\n🌐 STEP 2: FIRS Connectivity Test")
        results["firs_connectivity"] = await run_quick_firs_test()
        
        # Step 3: Full integrated test
        logger.info("\n🔄 STEP 3: Integrated Odoo-FIRS Test")
        results["integrated_test"] = await run_integrated_test()
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info("🎯 PHASE 2 INTEGRATION TEST SUMMARY")
        logger.info("="*80)
        
        passed_tests = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title().ljust(25)}: {status}")
        
        logger.info("="*80)
        
        if passed_tests == total_tests:
            logger.info("🎉 PHASE 2 INTEGRATION: COMPLETE SUCCESS")
            logger.info("✅ New platform architecture is fully operational!")
            logger.info("🚀 Ready to proceed with FIRS UAT submission!")
            return_code = 0
        else:
            success_rate = (passed_tests / total_tests) * 100
            logger.info(f"⚠️  PHASE 2 INTEGRATION: PARTIAL SUCCESS ({success_rate:.1f}%)")
            logger.info(f"🔧 {total_tests - passed_tests} component(s) need attention")
            
            if results["environment_validation"] and results["firs_connectivity"]:
                logger.info("✅ Core infrastructure is working - PHASE 2 can proceed with monitoring")
                return_code = 0
            else:
                logger.info("❌ Core infrastructure issues detected - address before PHASE 2")
                return_code = 1
        
        logger.info("="*80)
        return return_code
        
    except Exception as e:
        logger.error(f"❌ Test runner failed: {str(e)}")
        return 1


if __name__ == "__main__":
    if not TESTS_AVAILABLE:
        print("❌ Integration tests not available. Please check your Python path and dependencies.")
        sys.exit(1)
    
    return_code = asyncio.run(main())
    sys.exit(return_code)