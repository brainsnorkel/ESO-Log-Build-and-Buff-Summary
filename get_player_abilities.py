#!/usr/bin/env python3
"""
Get actual player abilities from ESO game data.
"""

import asyncio
import sys
from dotenv import load_dotenv

# Add src to path and load env
sys.path.append('src')
load_dotenv()

from src.eso_builds.api_client import ESOLogsClient

async def get_player_abilities():
    """Get real ESO player abilities."""
    print("🔍 Getting real ESO player abilities")
    print("=" * 60)
    
    async with ESOLogsClient() as client:
        try:
            # Get multiple pages to find player abilities
            all_abilities = []
            
            for page in range(1, 6):  # Get first 5 pages (250 abilities)
                print(f"📡 Fetching abilities page {page}...")
                response = await client._make_request(
                    'get_abilities',
                    limit=50,
                    page=page
                )
                
                if response and hasattr(response, 'game_data'):
                    abilities_data = response.game_data.abilities
                    if hasattr(abilities_data, 'data') and abilities_data.data:
                        all_abilities.extend(abilities_data.data)
                        print(f"  ✅ Got {len(abilities_data.data)} abilities from page {page}")
            
            print(f"\n🎯 Total abilities collected: {len(all_abilities)}")
            
            # Filter for actual player abilities (exclude GM/system abilities)
            player_abilities = []
            for ability in all_abilities:
                name = getattr(ability, 'name', '')
                if name and not any(exclude in name.upper() for exclude in ['GM ', 'TOOL', 'JUST ', 'DEBUG', 'TEST']):
                    player_abilities.append(ability)
            
            print(f"🎮 Player abilities found: {len(player_abilities)}")
            
            # Show some examples
            print(f"\n📋 Sample Player Abilities:")
            for i, ability in enumerate(player_abilities[:20]):
                ability_name = getattr(ability, 'name', 'Unknown')
                ability_id = getattr(ability, 'id', 'Unknown')
                print(f"  {i+1}. {ability_name} (ID: {ability_id})")
            
            # Look for common ESO skills by class
            print(f"\n🔍 Looking for class-specific abilities...")
            
            # Common DPS abilities
            dps_keywords = ['Crystal Fragments', 'Force Pulse', 'Elemental Weapon', 'Mage', 'Lightning', 'Fire', 'Ice', 'Destruction', 'Flame', 'Shock']
            dps_abilities = []
            
            # Common Tank abilities  
            tank_keywords = ['Taunt', 'Pierce Armor', 'Defensive', 'Shield', 'Block', 'Armor', 'Guard', 'Protection']
            tank_abilities = []
            
            # Common Healer abilities
            heal_keywords = ['Heal', 'Restoration', 'Recovery', 'Ward', 'Blessing', 'Prayer', 'Spring', 'Light']
            heal_abilities = []
            
            for ability in player_abilities:
                name = getattr(ability, 'name', '')
                if any(keyword in name for keyword in dps_keywords):
                    dps_abilities.append(name)
                elif any(keyword in name for keyword in tank_keywords):
                    tank_abilities.append(name)
                elif any(keyword in name for keyword in heal_keywords):
                    heal_abilities.append(name)
            
            print(f"\n🗡️ DPS Abilities Found ({len(dps_abilities)}):")
            for ability in dps_abilities[:10]:
                print(f"  • {ability}")
                
            print(f"\n🛡️ Tank Abilities Found ({len(tank_abilities)}):")
            for ability in tank_abilities[:10]:
                print(f"  • {ability}")
                
            print(f"\n💚 Healer Abilities Found ({len(heal_abilities)}):")
            for ability in heal_abilities[:10]:
                print(f"  • {ability}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(get_player_abilities())
