#!/usr/bin/env python3
"""
Debug script to see what the execute() method returns.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from src.eso_builds.api_client import ESOLogsClient

async def debug_execute_response():
    """Debug the execute() method response."""
    print("🔍 Debugging execute() method response")
    print("=" * 60)
    
    async with ESOLogsClient() as client:
        try:
            report_code = "mtFqVzQPNBcCrd1h"
            
            # Simple query first
            simple_query = """
            query GetReport($code: String!) {
              reportData {
                report(code: $code) {
                  code
                  title
                }
              }
            }
            """
            
            print(f"📡 Testing simple query...")
            response = await client._client.execute(simple_query, {'code': report_code})
            
            print(f"✅ Response type: {type(response)}")
            if hasattr(response, '__dict__'):
                print(f"📋 Response attributes: {list(response.__dict__.keys())}")
            else:
                print(f"📋 Response dir(): {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
            # Try to access different response structures
            structures_to_try = [
                ('response.data', lambda: response.data if hasattr(response, 'data') else None),
                ('response.reportData', lambda: response.reportData if hasattr(response, 'reportData') else None),
                ('response.report_data', lambda: response.report_data if hasattr(response, 'report_data') else None),
                ('response["data"]', lambda: response["data"] if isinstance(response, dict) and "data" in response else None),
                ('response["reportData"]', lambda: response["reportData"] if isinstance(response, dict) and "reportData" in response else None),
            ]
            
            for name, accessor in structures_to_try:
                try:
                    result = accessor()
                    if result is not None:
                        print(f"✅ {name}: {type(result)}")
                        if hasattr(result, '__dict__'):
                            print(f"    Attributes: {list(result.__dict__.keys())}")
                        elif isinstance(result, dict):
                            print(f"    Keys: {list(result.keys())}")
                    else:
                        print(f"❌ {name}: None")
                except Exception as e:
                    print(f"❌ {name}: Error - {e}")
            
            # Now try the master data query
            print(f"\n📡 Testing master data query...")
            master_query = """
            query GetReportMasterData($code: String!) {
              reportData {
                report(code: $code) {
                  masterData {
                    abilities {
                      gameID
                      name
                    }
                  }
                }
              }
            }
            """
            
            master_response = await client._client.execute(master_query, {'code': report_code})
            print(f"Master response type: {type(master_response)}")
            
            if hasattr(master_response, '__dict__'):
                print(f"Master response attributes: {list(master_response.__dict__.keys())}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_execute_response())
