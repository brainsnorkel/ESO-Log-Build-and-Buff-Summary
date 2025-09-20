#!/usr/bin/env python3
"""
Test the GameData abilities query to get real ESO abilities.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from src.eso_builds.api_client import ESOLogsClient

async def test_game_abilities():
    """Test the GameData abilities query."""
    print("🔍 Testing GameData abilities query")
    print("=" * 60)
    
    async with ESOLogsClient() as client:
        try:
            print("📡 Fetching game abilities...")
            response = await client._make_request(
                'get_abilities',
                limit=50,  # Get first 50 abilities
                page=1
            )
            
            print(f"✅ Response type: {type(response)}")
            
            if response and hasattr(response, 'game_data'):
                abilities_data = response.game_data.abilities
                print(f"✅ Abilities data: {type(abilities_data)}")
                
                if hasattr(abilities_data, 'data') and abilities_data.data:
                    abilities = abilities_data.data
                    print(f"🎯 Found {len(abilities)} abilities!")
                    
                    # Show first 10 abilities
                    print(f"\n📋 First 10 ESO Abilities:")
                    for i, ability in enumerate(abilities[:10]):
                        ability_id = getattr(ability, 'id', 'Unknown')
                        ability_name = getattr(ability, 'name', 'Unknown')
                        ability_icon = getattr(ability, 'icon', 'Unknown')
                        print(f"  {i+1}. ID: {ability_id}, Name: {ability_name}")
                        
                    # Look for common abilities
                    print(f"\n🔍 Looking for common ESO abilities...")
                    common_abilities = ['Crystal Fragments', 'Force Pulse', 'Elemental Weapon', 'Hardened Ward']
                    for ability in abilities:
                        ability_name = getattr(ability, 'name', '')
                        if any(common in ability_name for common in common_abilities):
                            print(f"  🎯 Found: {ability_name} (ID: {getattr(ability, 'id', 'Unknown')})")
                            
                else:
                    print("❌ No abilities data found")
            else:
                print("❌ No game_data in response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_game_abilities())
