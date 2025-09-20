#!/usr/bin/env python3
"""
Debug script to see what methods are available on the esologs Client.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from esologs import get_access_token, Client

async def debug_esologs_methods():
    """Debug the esologs Client methods."""
    print("🔍 Debugging esologs Client methods")
    print("=" * 60)
    
    try:
        # Get access token
        token = get_access_token()
        
        # Create client
        client = Client(
            url="https://www.esologs.com/api/v2/client",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"✅ Client created: {type(client)}")
        
        # List all methods
        methods = [method for method in dir(client) if not method.startswith('_') and callable(getattr(client, method))]
        print(f"📋 Available methods ({len(methods)}):")
        for i, method in enumerate(methods):
            print(f"  {i+1}. {method}")
        
        # Check for GraphQL-related methods
        graphql_methods = [method for method in methods if 'graph' in method.lower() or 'query' in method.lower() or 'execute' in method.lower()]
        if graphql_methods:
            print(f"\n🎯 GraphQL-related methods:")
            for method in graphql_methods:
                print(f"  • {method}")
        else:
            print("\n❌ No obvious GraphQL methods found")
            
        # Check if client has a way to execute custom queries
        custom_methods = [method for method in methods if any(keyword in method.lower() for keyword in ['custom', 'raw', 'execute', 'request', 'call'])]
        if custom_methods:
            print(f"\n🔧 Potential custom query methods:")
            for method in custom_methods:
                print(f"  • {method}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_esologs_methods())
