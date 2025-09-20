#!/usr/bin/env python3
"""
Debug script to understand the execute() method signature.
"""

import asyncio
import sys
from dotenv import load_dotenv
import inspect

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from esologs import get_access_token, Client

async def debug_execute_method():
    """Debug the execute() method signature."""
    print("🔍 Debugging execute() method signature")
    print("=" * 60)
    
    try:
        # Get access token
        token = get_access_token()
        
        # Create client
        client = Client(
            url="https://www.esologs.com/api/v2/client",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get the execute method
        execute_method = getattr(client, 'execute')
        
        # Get signature
        sig = inspect.signature(execute_method)
        print(f"✅ execute() signature: {sig}")
        
        # Get parameters
        params = list(sig.parameters.keys())
        print(f"📋 Parameters: {params}")
        
        # Try the method with correct order
        print(f"\n📡 Testing with operation first...")
        
        query = """
        query GetReport($code: String!) {
          reportData {
            report(code: $code) {
              code
              title
            }
          }
        }
        """
        
        variables = {'code': 'mtFqVzQPNBcCrd1h'}
        
        response = await client.execute(query, variables)
        print(f"✅ Response status: {response.status_code}")
        print(f"📄 Response content: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                print(f"✅ Query successful! Got data.")
            if 'errors' in data:
                print(f"❌ GraphQL errors: {data['errors']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_execute_method())
