#!/usr/bin/env python3
"""
Test script to verify connection to ESO Logs API.

This script tests the connection to esologs.com API using the esologs-python library.
You need to set up your API credentials before running this test.
"""

import os
import asyncio
from typing import Optional

# Try to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
except ImportError:
    pass  # python-dotenv not installed, skip .env file loading

try:
    from esologs import get_access_token, AsyncBaseClient, Client
    print("✅ esologs library imported successfully")
except ImportError as e:
    print(f"❌ Failed to import esologs library: {e}")
    exit(1)


def check_credentials() -> tuple[Optional[str], Optional[str]]:
    """Check if API credentials are available."""
    client_id = os.getenv('ESOLOGS_ID')
    client_secret = os.getenv('ESOLOGS_SECRET')
    
    print(f"ESOLOGS_ID: {'✅ Set' if client_id else '❌ Not set'}")
    print(f"ESOLOGS_SECRET: {'✅ Set' if client_secret else '❌ Not set'}")
    
    return client_id, client_secret


def test_authentication():
    """Test authentication with ESO Logs API."""
    print("\n🔐 Testing authentication...")
    
    try:
        # This will use environment variables ESOLOGS_ID and ESOLOGS_SECRET
        token = get_access_token()
        print("✅ Successfully obtained access token")
        print(f"Token preview: {token[:20]}..." if len(token) > 20 else f"Token: {token}")
        return token
    except ValueError as e:
        print(f"❌ Credentials error: {e}")
        return None
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


async def test_api_connection(token: str):
    """Test basic API connection."""
    print("\n🌐 Testing API connection...")
    
    try:
        client = Client(
            url="https://www.esologs.com/api/v2/client",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Try to get rate limit information as a simple API test
        rate_limit = await client.get_rate_limit_data()
        print("✅ Successfully connected to ESO Logs API")
        
        # Print available rate limit information
        if hasattr(rate_limit, 'limit_per_hour'):
            print(f"Rate limit: {getattr(rate_limit, 'points_spent_this_hour', 'N/A')}/{rate_limit.limit_per_hour} points per hour")
        elif hasattr(rate_limit, 'points_per_hour'):
            print(f"Rate limit: {getattr(rate_limit, 'points_spent_this_hour', 'N/A')}/{rate_limit.points_per_hour} points per hour")
        else:
            print(f"Rate limit data: {rate_limit}")
            
        if hasattr(rate_limit, 'limit_reset_time'):
            print(f"Rate limit resets at: {rate_limit.limit_reset_time}")
        elif hasattr(rate_limit, 'reset_time'):
            print(f"Rate limit resets at: {rate_limit.reset_time}")
            
        return True
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False


async def test_basic_query(token: str):
    """Test a basic API query."""
    print("\n📊 Testing basic API query...")
    
    try:
        client = Client(
            url="https://www.esologs.com/api/v2/client",
            headers={"Authorization": f"Bearer {token}"}
        )
        # Try to get zones as a simple test
        zones_response = await client.get_zones()
        if zones_response and hasattr(zones_response, 'zones') and zones_response.zones:
            zones = zones_response.zones
            print(f"✅ Successfully retrieved zone data")
            print(f"Found {len(zones)} zones")
            # Show first few zones as example
            for i, zone in enumerate(zones[:3]):
                print(f"  - Zone {i+1}: {zone.name}")
            if len(zones) > 3:
                print(f"  ... and {len(zones) - 3} more zones")
            return True
        elif zones_response:
            print(f"✅ Successfully retrieved zones response: {zones_response}")
            return True
        else:
            print("⚠️ Connected but no zone data returned")
            return False
    except Exception as e:
        print(f"❌ API query failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 ESO Logs API Connection Test")
    print("=" * 40)
    
    # Check credentials
    client_id, client_secret = check_credentials()
    
    if not client_id or not client_secret:
        print("\n❌ Missing API credentials!")
        print("\nTo fix this, you need to:")
        print("1. Register your application at https://www.esologs.com/api/clients")
        print("2. Get your client_id and client_secret")
        print("3. Set environment variables:")
        print("   export ESOLOGS_ID='your_client_id_here'")
        print("   export ESOLOGS_SECRET='your_client_secret_here'")
        print("\nOr create a .env file in your project root with:")
        print("   ESOLOGS_ID=your_client_id_here")
        print("   ESOLOGS_SECRET=your_client_secret_here")
        return False
    
    # Test authentication
    token = test_authentication()
    if not token:
        return False
    
    # Test API connection
    connection_ok = await test_api_connection(token)
    if not connection_ok:
        return False
    
    # Test basic query
    query_ok = await test_basic_query(token)
    
    if connection_ok and query_ok:
        print("\n🎉 All tests passed! ESO Logs API connection is working.")
        return True
    else:
        print("\n⚠️ Some tests failed, but basic connection is working.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        exit(1)
