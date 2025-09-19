#!/usr/bin/env python3
"""
Debug script to understand what the ESO Logs API is returning.
"""

import asyncio
import logging

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.eso_builds.api_client import ESOLogsClient

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def debug_api_methods():
    """Debug what methods are available and what they return."""
    print("🔍 Debugging ESO Logs API Methods")
    print("=" * 40)
    
    try:
        async with ESOLogsClient() as client:
            print("✅ API client connected")
            
            # Test different methods to see what's available
            print("\n📊 Testing get_reports method...")
            try:
                # Try without zone filter first
                reports = await client._make_request("get_reports", limit=5, page=1)
                print(f"✅ get_reports returned: {type(reports)}")
                if hasattr(reports, '__len__'):
                    print(f"   Length: {len(reports)}")
                if hasattr(reports, 'data'):
                    print(f"   Has data attribute")
                    if hasattr(reports.data, '__len__'):
                        print(f"   Data length: {len(reports.data)}")
                print(f"   Structure: {reports}")
                
            except Exception as e:
                print(f"❌ get_reports failed: {e}")
            
            print("\n📊 Testing get_reports with zone_id...")
            try:
                reports_with_zone = await client._make_request("get_reports", zone_id=19, limit=5, page=1)
                print(f"✅ get_reports with zone_id returned: {type(reports_with_zone)}")
                print(f"   Structure: {reports_with_zone}")
                
            except Exception as e:
                print(f"❌ get_reports with zone_id failed: {e}")
            
            print("\n📊 Testing specific report lookup...")
            try:
                specific_report = await client._make_request("get_report_by_code", code="mtFqVzQPNBcCrd1h")
                print(f"✅ get_report_by_code returned: {type(specific_report)}")
                if specific_report:
                    print(f"   Has fights: {hasattr(specific_report, 'fights')}")
                    if hasattr(specific_report, 'fights'):
                        print(f"   Fights: {specific_report.fights}")
                    print(f"   Structure: {specific_report}")
                else:
                    print("   Report is None or empty")
                
            except Exception as e:
                print(f"❌ get_report_by_code failed: {e}")
            
            print("\n📊 Available client methods:")
            methods = [method for method in dir(client._client) if not method.startswith('_') and 'get' in method.lower()]
            for method in methods:
                print(f"   - {method}")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")


async def main():
    """Main debug function."""
    await debug_api_methods()


if __name__ == "__main__":
    asyncio.run(main())
