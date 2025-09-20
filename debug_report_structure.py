#!/usr/bin/env python3
"""
Debug script to see what attributes are available on a report object.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from src.eso_builds.api_client import ESOLogsClient

async def debug_report_structure():
    """Debug the report object structure."""
    print("🔍 Debugging report object structure")
    print("=" * 60)
    
    async with ESOLogsClient() as client:
        try:
            report_code = "mtFqVzQPNBcCrd1h"
            
            print(f"📡 Fetching report {report_code}...")
            response = await client._make_request("get_report_by_code", code=report_code)
            
            if response and hasattr(response, 'report_data'):
                report = response.report_data.report
                print(f"✅ Report object type: {type(report)}")
                
                # List all attributes
                if hasattr(report, '__dict__'):
                    print(f"📋 Report attributes: {list(report.__dict__.keys())}")
                else:
                    print(f"📋 Report dir(): {[attr for attr in dir(report) if not attr.startswith('_')]}")
                
                # Check specific attributes
                attrs_to_check = ['masterData', 'master_data', 'abilities', 'actors', 'fights', 'code', 'title']
                for attr in attrs_to_check:
                    has_attr = hasattr(report, attr)
                    print(f"  {attr}: {'✅' if has_attr else '❌'}")
                    if has_attr:
                        value = getattr(report, attr)
                        print(f"    Type: {type(value)}")
                        if hasattr(value, '__len__'):
                            try:
                                print(f"    Length: {len(value)}")
                            except:
                                pass
            else:
                print("❌ No report data found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_report_structure())
