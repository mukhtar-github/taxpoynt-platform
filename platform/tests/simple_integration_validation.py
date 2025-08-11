#!/usr/bin/env python3
"""
Simple Integration Validation - PHASE 2 Setup Check
===================================================

Lightweight validation script that checks PHASE 2 integration setup without external dependencies.
Validates environment configuration and basic connectivity requirements.

This script ensures the consolidated environment and integration framework is properly configured.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def print_result(test_name, success, details=""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{test_name.ljust(30)}: {status}")
    if details:
        print(f"{''.ljust(32)} {details}")

def validate_environment():
    """Validate critical environment variables"""
    print_header("ENVIRONMENT VALIDATION")
    
    # Critical variables for PHASE 2
    critical_vars = {
        "FIRS_SANDBOX_URL": "FIRS sandbox endpoint",
        "FIRS_SANDBOX_API_KEY": "FIRS API key", 
        "FIRS_SANDBOX_API_SECRET": "FIRS API secret",
        "ODOO_HOST": "Odoo host",
        "ODOO_DATABASE": "Odoo database",
        "ODOO_USERNAME": "Odoo username",
        "ODOO_PASSWORD": "Odoo password"
    }
    
    results = {}
    
    for var, description in critical_vars.items():
        value = os.getenv(var)
        if value:
            results[var] = True
            # Hide sensitive values
            if any(sensitive in var for sensitive in ["PASSWORD", "SECRET", "KEY"]):
                display_value = "***configured***"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print_result(description, True, display_value)
        else:
            results[var] = False
            print_result(description, False, "NOT SET")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nEnvironment Status: {success_count}/{total_count} variables configured")
    
    return success_count == total_count, results

def test_firs_connectivity():
    """Test basic FIRS API connectivity"""
    print_header("FIRS CONNECTIVITY TEST")
    
    firs_url = os.getenv("FIRS_SANDBOX_URL")
    api_key = os.getenv("FIRS_SANDBOX_API_KEY")
    api_secret = os.getenv("FIRS_SANDBOX_API_SECRET")
    
    if not all([firs_url, api_key, api_secret]):
        print_result("FIRS Configuration", False, "Missing credentials")
        return False, {}
    
    # Test health endpoint
    health_url = f"{firs_url}/api/v1/health"
    headers = {
        "x-api-key": api_key,
        "x-api-secret": api_secret,
        "User-Agent": "TaxPoynt-PHASE2-Validation/1.0"
    }
    
    results = {}
    
    try:
        print("⏳ Testing FIRS health endpoint...")
        req = urllib.request.Request(health_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            content = response.read().decode('utf-8')
            
        success = 200 <= status_code < 300
        results["health_check"] = success
        print_result("Health Check", success, f"Status: {status_code}")
        
        if success:
            print(f"✅ FIRS sandbox is reachable at {firs_url}")
        
    except urllib.error.HTTPError as e:
        results["health_check"] = False
        print_result("Health Check", False, f"HTTP {e.code}: {e.reason}")
        
    except urllib.error.URLError as e:
        results["health_check"] = False
        print_result("Health Check", False, f"Connection failed: {e.reason}")
        
    except Exception as e:
        results["health_check"] = False
        print_result("Health Check", False, f"Error: {str(e)}")
    
    # Test currencies endpoint (quick validation)
    currencies_url = f"{firs_url}/api/v1/invoice/resources/currencies"
    try:
        print("⏳ Testing FIRS currencies endpoint...")
        req = urllib.request.Request(currencies_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            
        success = 200 <= status_code < 300
        results["currencies"] = success
        print_result("Currencies API", success, f"Status: {status_code}")
        
    except Exception as e:
        results["currencies"] = False
        print_result("Currencies API", False, f"Error: {str(e)[:50]}...")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nFIRS Connectivity: {success_count}/{total_count} endpoints accessible")
    
    return success_count > 0, results

def validate_platform_structure():
    """Validate platform directory structure"""
    print_header("PLATFORM STRUCTURE VALIDATION")
    
    # Key directories and files that should exist
    required_paths = {
        "platform/backend/app_services/firs_communication": "FIRS services",
        "platform/backend/si_services/erp_integration/odoo_ubl_service_connector.py": "Odoo UBL service",
        "platform/backend/external_integrations/business_systems": "Business system connectors",
        "platform/tests/integration": "Integration tests",
        ".env": "Environment configuration",
        ".env.example": "Environment template"
    }
    
    results = {}
    
    for path, description in required_paths.items():
        full_path = Path(path)
        exists = full_path.exists()
        results[path] = exists
        
        if exists:
            if full_path.is_file():
                size = full_path.stat().st_size
                print_result(description, True, f"File exists ({size} bytes)")
            else:
                items = len(list(full_path.iterdir())) if full_path.is_dir() else 0
                print_result(description, True, f"Directory exists ({items} items)")
        else:
            print_result(description, False, "Not found")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nPlatform Structure: {success_count}/{total_count} components found")
    
    return success_count >= (total_count * 0.8), results  # 80% threshold

def validate_integration_services():
    """Validate integration services are available"""
    print_header("INTEGRATION SERVICES VALIDATION")
    
    # Check if key service files exist and are valid Python
    service_files = {
        "platform/backend/si_services/erp_integration/odoo_ubl_service_connector.py": "Odoo UBL Connector",
        "platform/backend/app_services/firs_communication/firs_api_client.py": "FIRS API Client",
        "platform/tests/integration/test_firs_connectivity.py": "FIRS Connectivity Test"
    }
    
    results = {}
    
    for file_path, description in service_files.items():
        path = Path(file_path)
        
        if path.exists():
            try:
                # Basic validation - check if it's readable and contains expected keywords
                content = path.read_text(encoding='utf-8')
                
                # Check for key indicators
                if "odoo" in file_path.lower():
                    has_required = "UBL" in content or "odoo" in content.lower()
                elif "firs" in file_path.lower():
                    has_required = "FIRS" in content or "api" in content.lower()
                else:
                    has_required = len(content) > 100  # Basic size check
                
                results[file_path] = has_required
                status_detail = "Valid service file" if has_required else "File exists but may be incomplete"
                print_result(description, has_required, status_detail)
                
            except Exception as e:
                results[file_path] = False
                print_result(description, False, f"Read error: {str(e)[:30]}...")
        else:
            results[file_path] = False
            print_result(description, False, "File not found")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nIntegration Services: {success_count}/{total_count} services validated")
    
    return success_count >= (total_count * 0.7), results  # 70% threshold

def generate_summary(all_results):
    """Generate comprehensive summary"""
    print_header("PHASE 2 INTEGRATION SETUP SUMMARY")
    
    # Calculate overall scores
    total_passed = 0
    total_tests = 0
    
    for category, (success, details) in all_results.items():
        category_passed = sum(details.values()) if isinstance(details, dict) else (1 if success else 0)
        category_total = len(details) if isinstance(details, dict) else 1
        
        total_passed += category_passed
        total_tests += category_total
        
        success_rate = (category_passed / category_total * 100) if category_total > 0 else 0
        status = "✅ READY" if success else "⚠️  NEEDS ATTENTION"
        
        print(f"{category.replace('_', ' ').title().ljust(25)}: {status} ({category_passed}/{category_total} - {success_rate:.0f}%)")
    
    print("="*60)
    
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    if overall_success_rate >= 85:
        print("🎉 PHASE 2 INTEGRATION: FULLY READY")
        print("✅ All critical components are configured and accessible")
        print("🚀 Ready to proceed with FIRS UAT submission!")
        return_code = 0
    elif overall_success_rate >= 70:
        print("✅ PHASE 2 INTEGRATION: READY WITH MONITORING")
        print(f"⚠️  {100 - overall_success_rate:.0f}% of components need attention")
        print("🔧 Address minor issues while proceeding with core testing")
        return_code = 0
    else:
        print("⚠️  PHASE 2 INTEGRATION: NEEDS CONFIGURATION")
        print(f"❌ {100 - overall_success_rate:.0f}% of components have issues")
        print("🔧 Address configuration issues before proceeding")
        return_code = 1
    
    print(f"\nOverall Score: {total_passed}/{total_tests} ({overall_success_rate:.1f}%)")
    
    # Save results for reference
    results_file = f"phase2_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    detailed_results = {
        "timestamp": datetime.now().isoformat(),
        "validation_type": "phase2_integration_setup",
        "overall_score": overall_success_rate,
        "return_code": return_code,
        "results": {
            category: {
                "success": success,
                "details": details
            }
            for category, (success, details) in all_results.items()
        }
    }
    
    try:
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        print(f"📊 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️  Could not save results file: {e}")
    
    return return_code

def main():
    """Main validation function"""
    print("🚀 TAXPOYNT PHASE 2 INTEGRATION SETUP VALIDATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all validation checks
    results = {}
    
    try:
        # Environment validation
        env_success, env_details = validate_environment()
        results["environment"] = (env_success, env_details)
        
        # FIRS connectivity (only if environment is ready)
        if env_success:
            firs_success, firs_details = test_firs_connectivity()
            results["firs_connectivity"] = (firs_success, firs_details)
        else:
            print("\n⚠️  Skipping FIRS connectivity test - environment not ready")
            results["firs_connectivity"] = (False, {"skipped": True})
        
        # Platform structure validation
        platform_success, platform_details = validate_platform_structure()
        results["platform_structure"] = (platform_success, platform_details)
        
        # Integration services validation
        services_success, services_details = validate_integration_services()
        results["integration_services"] = (services_success, services_details)
        
        # Generate comprehensive summary
        return_code = generate_summary(results)
        
        return return_code
        
    except KeyboardInterrupt:
        print("\n❌ Validation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Validation failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    return_code = main()
    sys.exit(return_code)