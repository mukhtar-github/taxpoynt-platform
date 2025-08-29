#!/usr/bin/env python3
"""
SDK Data Seeding Script
======================
Command-line script to seed SDK management data into the database.
Can be run standalone or as part of deployment process.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core_platform.services.sdk_data_seeder import seed_sdk_data

async def main():
    parser = argparse.ArgumentParser(description="Seed SDK management data")
    parser.add_argument(
        "--force-refresh", 
        action="store_true", 
        help="Force refresh existing data"
    )
    parser.add_argument(
        "--environment", 
        default="development",
        choices=["development", "staging", "production"],
        help="Environment to seed data for"
    )
    
    args = parser.parse_args()
    
    print(f"🔄 Starting SDK data seeding for {args.environment} environment...")
    
    if args.environment == "production":
        print("⚠️  Production environment detected")
        if not args.force_refresh:
            response = input("Are you sure you want to seed production data? (y/N): ")
            if response.lower() != 'y':
                print("❌ Seeding cancelled")
                return
    
    try:
        # Set environment variables if needed
        if "USE_DEMO_DATA" not in os.environ:
            os.environ["USE_DEMO_DATA"] = "false"
        if "DEMO_MODE" not in os.environ:
            os.environ["DEMO_MODE"] = "false" if args.environment == "production" else "true"
        
        # Run seeding
        results = await seed_sdk_data(force_refresh=args.force_refresh)
        
        print("\n✅ SDK data seeding completed successfully!")
        print(f"📊 Results:")
        print(f"   • SDKs created/updated: {results['sdks_created']}")
        print(f"   • Scenarios created/updated: {results['scenarios_created']}")
        print(f"   • Documentation created/updated: {results['documentation_created']}")
        print(f"   • Analytics records created/updated: {results['analytics_created']}")
        
        if results.get("errors"):
            print(f"\n⚠️  Warnings/Errors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"   • {error}")
        
    except Exception as e:
        print(f"\n❌ SDK data seeding failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())