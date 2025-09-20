#!/usr/bin/env python3
"""
Debug script to see the actual content of the execute() response.
"""

import asyncio
import sys
import json
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from src.eso_builds.api_client import ESOLogsClient

async def debug_response_content():
    """Debug the execute() method response content."""
    print("🔍 Debugging execute() method response content")
    print("=" * 60)
    
    async with ESOLogsClient() as client:
        try:
            report_code = "mtFqVzQPNBcCrd1h"
            
            # Master data query
            query = """
            query GetReportMasterData($code: String!) {
              reportData {
                report(code: $code) {
                  masterData {
                    abilities {
                      gameID
                      name
                      icon
                      type
                    }
                    actors(type: "Player") {
                      name
                      id
                      gameID
                      type
                    }
                  }
                }
              }
            }
            """
            
            print(f"📡 Executing master data query...")
            response = await client._client.execute(query, {'code': report_code})
            
            print(f"✅ Response status: {response.status_code}")
            print(f"📋 Response headers: {dict(response.headers)}")
            
            # Get the content
            content = response.text
            print(f"📄 Response content length: {len(content)}")
            print(f"📄 First 500 chars: {content[:500]}")
            
            # Try to parse as JSON
            try:
                data = response.json()
                print(f"✅ JSON parsed successfully!")
                print(f"📋 JSON keys: {list(data.keys())}")
                
                if 'data' in data:
                    print(f"✅ 'data' key found!")
                    data_section = data['data']
                    print(f"📋 Data keys: {list(data_section.keys())}")
                    
                    if 'reportData' in data_section:
                        print(f"✅ 'reportData' key found!")
                        report_data = data_section['reportData']
                        if report_data and 'report' in report_data:
                            print(f"✅ 'report' key found!")
                            report = report_data['report']
                            if report and 'masterData' in report:
                                print(f"✅ 'masterData' key found!")
                                master_data = report['masterData']
                                print(f"📋 Master data keys: {list(master_data.keys()) if master_data else 'None'}")
                                
                                if master_data and 'abilities' in master_data:
                                    abilities = master_data['abilities']
                                    print(f"🎯 Found {len(abilities)} abilities!")
                                    if abilities:
                                        print(f"📋 First ability: {abilities[0]}")
                                else:
                                    print(f"❌ No abilities in masterData")
                            else:
                                print(f"❌ No masterData in report")
                        else:
                            print(f"❌ No report in reportData")
                    else:
                        print(f"❌ No reportData in data")
                else:
                    print(f"❌ No 'data' key in JSON")
                
                if 'errors' in data:
                    print(f"❌ GraphQL errors: {data['errors']}")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_response_content())
